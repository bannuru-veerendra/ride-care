/**
 * Global TypeScript types shared across features.
 * Feature-specific types live inside their own feature folder.
 */

export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}
