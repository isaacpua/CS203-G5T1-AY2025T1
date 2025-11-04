import React, { useEffect, useState } from 'react';
import { getNewsletter } from "@/api/axiosClient";

function Newsletter() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    getNewsletter()
      .then((res) => {
        if (!mounted) return;
        setData(res.data);
      })
      .catch((err) => {
        if (!mounted) return;
        console.error('Failed to load newsletter:', err);
        setError(err);
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  if (loading) return <div>Loading newsletter...</div>;
  if (error) return <div>Error loading newsletter.</div>;

  return (
    <div>
      <h1>Newsletter</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
export default Newsletter;