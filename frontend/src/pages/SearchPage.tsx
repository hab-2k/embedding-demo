import { useState } from "react";
import SearchBar from "../components/SearchBar";
import ResultCard from "../components/ResultCard";
import { searchTranscripts } from "../api/client";
import type { SearchResult } from "../api/client";

export default function SearchPage() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (q: string) => {
    setIsLoading(true);
    setError(null);
    setQuery(q);
    try {
      const res = await searchTranscripts(q);
      setResults(res.results);
      setHasSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-lloyds-black tracking-tight">
          Transcript Search
        </h1>
        <p className="text-sm text-lloyds-grey-dark mt-2">
          Semantically search across call centre transcripts
        </p>
      </div>

      <SearchBar onSearch={handleSearch} isLoading={isLoading} />

      {error && (
        <div className="mt-8 bg-red-50 border border-red-200 rounded-xl p-4 max-w-2xl mx-auto">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {hasSearched && !isLoading && results.length === 0 && !error && (
        <div className="mt-12 text-center">
          <p className="text-sm text-lloyds-grey-dark">
            No results found for "{query}"
          </p>
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-8 space-y-3">
          <p className="text-xs text-lloyds-grey-dark font-medium uppercase tracking-wider mb-4">
            {results.length} result{results.length !== 1 ? "s" : ""}
          </p>
          {results.map((result) => (
            <ResultCard key={result.chunk_id} result={result} query={query} />
          ))}
        </div>
      )}
    </div>
  );
}
