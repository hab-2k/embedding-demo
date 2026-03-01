import { useState, useRef, DragEvent } from "react";
import { ingestCSV } from "../api/client";
import type { IngestResponse } from "../api/client";

export default function UploadPanel() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      setError("Please upload a .csv file");
      return;
    }
    setIsUploading(true);
    setError(null);
    setResult(null);
    try {
      const res = await ingestCSV(file);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const onDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className="max-w-xl mx-auto">
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => fileRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
          isDragging
            ? "border-lloyds-green bg-lloyds-green-light"
            : "border-lloyds-grey-mid hover:border-lloyds-green/50 bg-white"
        }`}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".csv"
          onChange={onFileChange}
          className="hidden"
        />

        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            <svg className="animate-spin h-8 w-8 text-lloyds-green" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm text-lloyds-grey-dark">
              Processing transcripts...
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <svg className="w-10 h-10 text-lloyds-grey-dark/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <div>
              <p className="text-sm font-medium text-lloyds-black">
                Drop your CSV here, or click to browse
              </p>
              <p className="text-xs text-lloyds-grey-dark mt-1">
                Expects columns: transcript_id, transcript_index, text
              </p>
            </div>
          </div>
        )}
      </div>

      {result && (
        <div className="mt-6 bg-lloyds-green-50 border border-lloyds-green/20 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-lloyds-green mb-3">
            Ingest Complete
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-lloyds-black">
                {result.chunks_written.toLocaleString()}
              </p>
              <p className="text-xs text-lloyds-grey-dark mt-0.5">
                Chunks Written
              </p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-lloyds-black">
                {result.transcripts_processed.toLocaleString()}
              </p>
              <p className="text-xs text-lloyds-grey-dark mt-0.5">
                Transcripts
              </p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-lloyds-black">
                {result.time_taken_seconds}s
              </p>
              <p className="text-xs text-lloyds-grey-dark mt-0.5">
                Time Taken
              </p>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-sm text-red-700 font-medium">{error}</p>
        </div>
      )}
    </div>
  );
}
