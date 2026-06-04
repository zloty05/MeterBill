import { useEffect, useRef, useState } from "react";

type AsyncState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

/**
 * Pobiera dane przez podaną funkcję async i śledzi loading/error.
 * `deps` wyzwala ponowne pobranie (jak useEffect). `reload()` ręcznie odświeża.
 * Funkcję trzymamy w ref, by nie wymuszać useCallback po stronie wywołującego.
 */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    fnRef.current()
      .then((d) => {
        if (alive) setData(d);
      })
      .catch((e: unknown) => {
        if (alive) setError(e instanceof Error ? e.message : "Nieznany błąd");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { data, loading, error, reload: () => setTick((t) => t + 1) };
}
