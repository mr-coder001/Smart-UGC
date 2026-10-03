import axios from "axios";
import { Asset, AdminStats, SearchResult } from "../types/asset";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const ADMIN_API_KEY = import.meta.env.VITE_ADMIN_API_KEY || "dev_admin_secret_key_123";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Admin Client with X-Admin-API-Key
export const adminClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
    "X-Admin-API-Key": ADMIN_API_KEY,
  },
});

export const apiService = {
  async getHealth() {
    const res = await apiClient.get("/health");
    return res.data;
  },

  async uploadAsset(file: File, onProgress?: (pct: number) => void): Promise<Asset> {
    const formData = new FormData();
    formData.append("file", file);

    const res = await apiClient.post<Asset>("/assets", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
    return res.data;
  },

  async getAssets(params?: {
    query?: string;
    tag?: string;
    page?: number;
    page_size?: number;
    sort_by?: string;
    sort_order?: string;
    quality_tier?: string;
    review_decision?: string;
    recommended_use?: string;
  }): Promise<SearchResult> {
    const res = await apiClient.get<SearchResult>("/assets", { params });
    return res.data;
  },

  async getAssetById(id: string): Promise<Asset> {
    const res = await apiClient.get<Asset>(`/assets/${id}`);
    return res.data;
  },

  async reanalyzeAsset(id: string): Promise<Asset> {
    const res = await apiClient.post<Asset>(`/assets/${id}/intelligence/analyze`);
    return res.data;
  },

  async deleteAsset(id: string): Promise<void> {
    await apiClient.delete(`/assets/${id}`);
  },

  async transformAsset(
    id: string,
    params: {
      width?: number;
      height?: number;
      crop?: string;
      gravity?: string;
      background_removal?: boolean;
      format?: string;
      quality?: string;
    }
  ) {
    const res = await apiClient.get(`/assets/${id}/transform`, { params });
    return res.data;
  },

  // Admin Methods
  async getAdminAssets(params?: {
    status?: string;
    tag?: string;
    query?: string;
    page?: number;
    page_size?: number;
  }): Promise<SearchResult> {
    const res = await adminClient.get<SearchResult>("/admin/assets", { params });
    return res.data;
  },

  async getAdminStats(): Promise<AdminStats> {
    const res = await adminClient.get<AdminStats>("/admin/stats");
    return res.data;
  },

  async approveAsset(id: string, reason?: string): Promise<Asset> {
    const res = await adminClient.post<Asset>(`/admin/assets/${id}/approve`, { reason });
    return res.data;
  },

  async rejectAsset(id: string, reason?: string): Promise<Asset> {
    const res = await adminClient.post<Asset>(`/admin/assets/${id}/reject`, { reason });
    return res.data;
  },
};
