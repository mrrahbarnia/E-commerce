from typing import Annotated, NewType, TypedDict, Generic, TypeVar, Callable

import sqlalchemy as sa
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from pydantic import BaseModel, Field

Limit = NewType("Limit", int)
Offset = NewType("Offset", int)

T = TypeVar("T")


class PaginationMeta(TypedDict):
    total_items: int
    total_pages: int
    current_page: int
    next_page_link: str | None
    prev_page_link: str | None


class PaginatedResponse(BaseModel, Generic[T]):
    result: list[T]
    meta: PaginationMeta


class PaginationQueryParamsSchema(BaseModel):
    page: Annotated[int, Field(ge=1)]
    per_page: Annotated[int, Field(ge=1)]

    def to_limit(self) -> tuple[Limit, Offset]:
        offset = (self.page - 1) * self.per_page
        return Limit(self.per_page), Offset(offset)


async def apply_pagination(
    request: Request,
    session: AsyncSession,
    query: Select,
    pagination_query: PaginationQueryParamsSchema,
    mapper_fn: Callable[[tuple], T],
) -> PaginatedResponse[T]:
    limit, offset = pagination_query.to_limit()
    total_items = await session.scalar(
        sa.select(sa.func.count()).select_from(query.subquery())
    )
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)

    raw_result = list((await session.execute(query)).tuples().all())
    mapped_result = [mapper_fn(row) for row in raw_result]

    total_items = total_items if total_items else 0
    total_pages = ((total_items + limit - 1) // limit) if total_items > 0 else 0

    next_page = (
        pagination_query.page + 1 if pagination_query.page < total_pages else None
    )
    next_url = (
        str(request.url.include_query_params(page=next_page)) if next_page else None
    )

    previous_page = pagination_query.page - 1 if pagination_query.page > 1 else None
    prev_url = (
        str(request.url.include_query_params(page=previous_page))
        if previous_page
        else None
    )

    return PaginatedResponse[T](
        result=mapped_result,
        meta={
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": pagination_query.page,
            "next_page_link": next_url,
            "prev_page_link": prev_url,
        },
    )
