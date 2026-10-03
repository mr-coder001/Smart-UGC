import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, CheckCircle2, AlertCircle, FileImage, ArrowRight, Loader2, ShieldCheck } from "lucide-react";
import { apiService } from "../services/api";
import { Asset } from "../types/asset";

const ALLOWED_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
  "image/avif",
  "image/heic",
  "image/heif",
];
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadedAsset, setUploadedAsset] = useState<Asset | null>(null);

  const validateAndSetFile = (file: File) => {
    setErrorMessage(null);
    setUploadedAsset(null);

    if (!ALLOWED_TYPES.includes(file.type)) {
      setErrorMessage(`Unsupported format: ${file.type || "unknown"}. Please upload JPEG, PNG, WebP, GIF, AVIF, or HEIC.`);
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMessage("File exceeds 10 MB limit.");
      return;
    }

    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setErrorMessage(null);
    setUploadProgress(10);

    try {
      const asset = await apiService.uploadAsset(selectedFile, (progress) => {
        setUploadProgress(progress);
      });
      setUploadedAsset(asset);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || "Upload failed. Please try again.";
      setErrorMessage(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white">Upload Asset</h1>
        <p className="mt-2 text-sm text-slate-400">
          Upload images up to 10 MB. Assets undergo automated MIME validation, AI scene detection, and enter the moderation queue.
        </p>
      </div>

      {/* Upload Box */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-3xl p-10 text-center cursor-pointer transition-all duration-300 flex flex-col items-center justify-center min-h-[300px] ${
          dragActive
            ? "border-indigo-400 bg-indigo-500/10 scale-[1.01]"
            : "border-slate-800 hover:border-slate-700 bg-slate-900/40"
        } ${isUploading ? "opacity-60 cursor-not-allowed" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ALLOWED_TYPES.join(",")}
          onChange={handleFileChange}
          className="hidden"
          disabled={isUploading}
        />

        {previewUrl ? (
          <div className="space-y-4 max-w-sm">
            <div className="relative mx-auto rounded-2xl overflow-hidden border border-slate-700 shadow-2xl">
              <img src={previewUrl} alt="Preview" className="max-h-64 w-auto object-contain mx-auto" />
            </div>
            <div className="text-xs text-slate-300 font-mono">
              {selectedFile?.name} ({(selectedFile?.size! / (1024 * 1024)).toFixed(2)} MB)
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto border border-indigo-500/20">
              <UploadCloud className="w-8 h-8" />
            </div>
            <div>
              <p className="text-base font-medium text-slate-200">
                Drag and drop your image here, or <span className="text-indigo-400 underline">browse</span>
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Supports JPEG, PNG, WebP, GIF, AVIF, HEIC (Max 10MB)
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      {isUploading && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-slate-400">
            <span className="flex items-center space-x-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
              <span>Uploading and analyzing image signature...</span>
            </span>
            <span className="font-mono">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-indigo-500 to-cyan-400 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="flex items-start space-x-3 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" />
          <div>
            <p className="font-semibold">Validation Error</p>
            <p className="text-xs text-rose-300/80 mt-0.5">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Upload Action Button */}
      {selectedFile && !uploadedAsset && !isUploading && (
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => {
              setSelectedFile(null);
              setPreviewUrl(null);
            }}
            className="px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-sm font-medium hover:bg-slate-800 transition"
          >
            Clear
          </button>
          <button
            type="button"
            onClick={handleUpload}
            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/30 transition flex items-center space-x-2"
          >
            <span>Proceed to Upload</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Success Banner */}
      {uploadedAsset && (
        <div className="p-6 rounded-3xl glass-card border-emerald-500/30 space-y-4">
          <div className="flex items-start space-x-3 text-emerald-400">
            <CheckCircle2 className="w-6 h-6 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-base text-white">Upload & Ingestion Successful</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Asset created with ID <span className="font-mono text-cyan-300">{uploadedAsset.public_id}</span>.{" "}
                Status:{" "}
                {uploadedAsset.status === "APPROVED" ? (
                  <span className="font-semibold text-emerald-400">
                    APPROVED (Auto-Approved by UGC Intelligence)
                  </span>
                ) : uploadedAsset.status === "REJECTED" ? (
                  <span className="font-semibold text-rose-400">
                    REJECTED (Content Policy Flagged)
                  </span>
                ) : (
                  <span className="font-semibold text-amber-400">
                    PENDING (Awaiting Moderation Review)
                  </span>
                )}
              </p>
            </div>
          </div>

          {/* AI Tags Preview */}
          <div className="pt-2 border-t border-slate-800">
            <span className="text-xs text-slate-400 block mb-2 font-medium">AI Detected Scene Tags:</span>
            {uploadedAsset.tags && uploadedAsset.tags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {uploadedAsset.tags.map((t) => (
                  <span
                    key={t.id}
                    className="px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-mono"
                  >
                    #{t.tag}{t.confidence != null ? ` (${(t.confidence * 100).toFixed(0)}%)` : ""}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No automated visual scene tags detected from provider.</p>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-end gap-2 pt-2">
            <button
              onClick={() => {
                setSelectedFile(null);
                setPreviewUrl(null);
                setUploadedAsset(null);
              }}
              className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-800 transition"
            >
              Upload Another
            </button>
            {uploadedAsset.status === "PENDING" && (
              <button
                onClick={() => navigate("/admin/moderation")}
                className="px-4 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-semibold flex items-center space-x-1.5 transition shadow-sm"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Go to Moderation Queue</span>
              </button>
            )}
            <button
              onClick={() => navigate(`/assets/${uploadedAsset.public_id}`)}
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition flex items-center space-x-1.5"
            >
              <span>View Asset Details</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
