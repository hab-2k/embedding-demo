import UploadPanel from "../components/UploadPanel";

export default function IngestPage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-lloyds-black tracking-tight">
          Ingest Transcripts
        </h1>
        <p className="text-sm text-lloyds-grey-dark mt-1">
          Upload a CSV of call transcripts to chunk, embed, and index
        </p>
      </div>
      <UploadPanel />
    </div>
  );
}
