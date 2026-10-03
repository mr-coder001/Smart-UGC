import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { RootLayout } from "./layouts/RootLayout";
import { GalleryPage } from "./pages/GalleryPage";
import { UploadPage } from "./pages/UploadPage";
import { AssetDetailPage } from "./pages/AssetDetailPage";
import { AdminModerationPage } from "./pages/AdminModerationPage";
import { AdminStatsPage } from "./pages/AdminStatsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RootLayout />}>
            <Route index element={<GalleryPage />} />
            <Route path="upload" element={<UploadPage />} />
            <Route path="assets/:id" element={<AssetDetailPage />} />
            <Route path="admin" element={<Navigate to="/admin/moderation" replace />} />
            <Route path="admin/moderation" element={<AdminModerationPage />} />
            <Route path="admin/stats" element={<AdminStatsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
