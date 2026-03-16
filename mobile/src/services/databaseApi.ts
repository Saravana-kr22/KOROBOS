/*
KOROBOS — Mobile Database API Service

Type-safe API methods for database operations.
*/

import { apiClient } from "./apiClient";

export interface Database {
  id: string;
  user_id: string;
  name: string;
  icon?: string;
  description?: string;
  properties: Property[];
  created_at: string;
  updated_at: string;
}

export interface Property {
  id: string;
  database_id: string;
  name: string;
  type: string;
  options?: Record<string, unknown>;
  position: number;
  created_at: string;
}

export interface DatabaseRecord {
  id: string;
  database_id: string;
  note_id?: string;
  values: RecordValue[];
  created_at: string;
  updated_at: string;
}

export interface RecordValue {
  property_id: string;
  value?: string;
}

export interface DatabaseListResponse {
  databases: Database[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface RecordListResponse {
  records: DatabaseRecord[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

/**
 * Database API methods for mobile app
 */
export const databaseApi = {
  // ── Databases ──

  /**
   * List all databases for authenticated user
   */
  async listDatabases(page = 1, limit = 20): Promise<DatabaseListResponse> {
    return apiClient.get("/databases", {
      page: page.toString(),
      limit: limit.toString(),
    });
  },

  /**
   * Get database by ID
   */
  async getDatabase(databaseId: string): Promise<Database> {
    return apiClient.get(`/databases/${databaseId}`);
  },

  /**
   * Create new database
   */
  async createDatabase(data: {
    name: string;
    icon?: string;
    description?: string;
  }): Promise<Database> {
    return apiClient.post("/databases", data);
  },

  /**
   * Update database
   */
  async updateDatabase(
    databaseId: string,
    data: {
      name?: string;
      icon?: string;
      description?: string;
    },
  ): Promise<Database> {
    return apiClient.put(`/databases/${databaseId}`, data);
  },

  /**
   * Delete database
   */
  async deleteDatabase(databaseId: string): Promise<void> {
    return apiClient.delete(`/databases/${databaseId}`);
  },

  // ── Properties ──

  /**
   * Add property to database
   */
  async addProperty(
    databaseId: string,
    data: {
      name: string;
      type: string;
      options?: Record<string, unknown>;
      position?: number;
    },
  ): Promise<Property> {
    return apiClient.post(`/databases/${databaseId}/properties`, data);
  },

  /**
   * Delete property
   */
  async deleteProperty(databaseId: string, propertyId: string): Promise<void> {
    return apiClient.delete(
      `/databases/${databaseId}/properties/${propertyId}`,
    );
  },

  // ── Records ──

  /**
   * List records with optional filtering and sorting
   */
  async listRecords(
    databaseId: string,
    options?: {
      page?: number;
      limit?: number;
      filter_property_id?: string | string[];
      filter_operator?: string | string[];
      filter_value?: string | string[];
      filterPropertyId?: string[];
      filterOperator?: string[];
      filterValue?: string[];
      sortPropertyId?: string;
      sort_property_id?: string;
      sortDirection?: "asc" | "desc";
      sort_direction?: "asc" | "desc";
    },
  ): Promise<RecordListResponse> {
    const params: Record<string, string> = {
      page: (options?.page || 1).toString(),
      limit: (options?.limit || 20).toString(),
    };

    // Support both snake_case and camelCase
    const filterPropId =
      options?.filter_property_id || options?.filterPropertyId;
    const filterOp = options?.filter_operator || options?.filterOperator;
    const filterVal = options?.filter_value || options?.filterValue;

    if (filterPropId) {
      const propId = Array.isArray(filterPropId)
        ? filterPropId[0]
        : filterPropId;
      if (propId) params["filter_property_id"] = propId;
    }

    if (filterOp) {
      const op = Array.isArray(filterOp) ? filterOp[0] : filterOp;
      if (op) params["filter_operator"] = op;
    }

    if (filterVal) {
      const val = Array.isArray(filterVal) ? filterVal[0] : filterVal;
      if (val) params["filter_value"] = val;
    }

    const sortPropId = options?.sort_property_id || options?.sortPropertyId;
    const sortDir = options?.sort_direction || options?.sortDirection;
    if (sortPropId) {
      params["sort_property_id"] = sortPropId;
      params["sort_direction"] = sortDir || "asc";
    }

    return apiClient.get(`/databases/${databaseId}/records`, params);
  },

  /**
   * Create record with values
   */
  async createRecord(
    databaseId: string,
    data: {
      values: Record<string, string>;
      note_id?: string;
    },
  ): Promise<DatabaseRecord> {
    return apiClient.post(`/databases/${databaseId}/records`, data);
  },

  /**
   * Update record values
   */
  async updateRecord(
    recordId: string,
    data: {
      values: Record<string, string>;
      note_id?: string;
    },
  ): Promise<DatabaseRecord> {
    return apiClient.put(`/records/${recordId}`, data);
  },

  /**
   * Delete record
   */
  async deleteRecord(recordId: string): Promise<void> {
    return apiClient.delete(`/records/${recordId}`);
  },
};

export default databaseApi;
