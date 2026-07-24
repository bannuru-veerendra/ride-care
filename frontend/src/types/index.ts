/**
 * Global TypeScript types shared across features.
 * Feature-specific types live inside their own feature folder.
 */

export interface ApiError {
  detail: string;
}

/**
 * Cursor-based paginated response from the API.
 * Pass next_cursor as ?cursor= in the next request.
 */
export interface CursorPage<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total: number;
}
