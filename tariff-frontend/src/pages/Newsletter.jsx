import React, { useEffect, useState } from 'react';
import { getNewsletter } from "@/api/axiosClient";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';




function splitIntoItems(md) {
  if (!md) return [];
  // Split by horizontal rules or ## headers
  const pattern = /\[[\s]*!\[.*\n#+.*\n.*ago\n/g
  const items = md.match(pattern)
  return items;
}



function Newsletter() {
  const [grid, setGrid] = useState(null);
  const [list, setList] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    getNewsletter()
      .then((res) => {
        if (!mounted) return;
        const md = res.data.markdown

        // console.log(md)
        const newsItems = splitIntoItems(md)
        console.log("Number of news items: " + newsItems.length)
        for (const item of newsItems) {
          console.log("New item!")
          console.log(item)
        }
        setGrid(newsItems.slice(0, 6)); // First 6 items for the grid
        setList(newsItems.slice(6)); // Remaining items
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
    <div className="container mx-auto px-4 py-8">
      <header className="max-w-4xl mx-auto text-center mb-10">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-sky-600 to-indigo-600">
          Tariff Newsletter
        </h1>
        <p className="mt-3 text-lg text-muted-foreground max-w-2xl mx-auto dark:text-gray-300">
          Curated news and analyses
        </p>
      </header>

      {/* Grid Layout for first 6 items */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {grid?.map((item, idx) => (
          <article 
            key={idx} 
            className="bg-card text-card-foreground rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow border border-border"
          >
            <div className="p-6">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    img: ({node, ...props}) => (
                      <img 
                        {...props} 
                        className="w-full h-48 object-cover rounded-md mb-4 border border-border" 
                        loading="lazy"
                      />
                    ),
                    h1: ({node, ...props}) => (
                      <h1 {...props} className="text-xl font-bold mb-3 text-foreground" />
                    ),
                    h2: ({node, ...props}) => (
                      <h2 {...props} className="text-lg font-semibold mb-2 text-foreground" />
                    ),
                    p: ({node, ...props}) => (
                      <p {...props} className="mb-3 line-clamp-3 text-muted-foreground" />
                    ),
                    a: ({node, ...props}) => (
                      <a {...props} className="text-primary hover:text-primary/80 transition-colors" />
                    ),
                  }}
                >
                  {item}
                </ReactMarkdown>
              </div>
            </div>
          </article>
        ))}
      </div>

      {/* List Layout for remaining items */}
      <div className="space-y-8">
        {list?.map((item, idx) => (
          <article 
            key={idx} 
            className="bg-card text-card-foreground rounded-lg shadow-sm p-6 border border-border"
          >
            <div className="prose max-w-none dark:prose-invert">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  img: ({node, ...props}) => (
                    <img 
                      {...props} 
                      className="max-w-full h-auto my-4 rounded-lg shadow-md border border-border"
                      loading="lazy"
                    />
                  ),
                  h1: ({node, ...props}) => (
                    <h1 {...props} className="text-xl font-bold mb-3 text-foreground" />
                  ),
                  h2: ({node, ...props}) => (
                    <h2 {...props} className="text-lg font-semibold mb-2 text-foreground" />
                  ),
                  p: ({node, ...props}) => (
                    <p {...props} className="mb-3 text-muted-foreground" />
                  ),
                  a: ({node, ...props}) => (
                    <a {...props} className="text-primary hover:text-primary/80 transition-colors" />
                  ),
                }}
              >
                {item}
              </ReactMarkdown>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

export default Newsletter;
