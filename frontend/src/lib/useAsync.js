// Hook para cargar datos con estados de carga/error y recarga periodica (Responsable: Gabriel).
import { useCallback, useEffect, useRef, useState } from "react";

export default function useAsync(fn, deps, { refreshMs } = {}) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const run = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const result = await fnRef.current();
      setData(result);
      setError(null);
      return result;
    } catch (err) {
      setError(err);
      return null;
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    run();
    if (!refreshMs) return undefined;
    const id = setInterval(() => run(true), refreshMs);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error, loading, reload: run, setData };
}
