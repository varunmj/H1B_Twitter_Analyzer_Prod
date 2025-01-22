"use client";

import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from "recharts";
import { Tweet } from "react-tweet";

export default function Home() {
  const [tweets, setTweets] = useState([]);
  const [sentiments, setSentiments] = useState({ positive: 0, neutral: 0, negative: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchData() {
      try {
        const tweetsResponse = await fetch("/api/tweets");
        if (!tweetsResponse.ok) throw new Error("Failed to fetch tweets");
        const tweetsData = await tweetsResponse.json();
        setTweets(tweetsData.tweets || []);

        const sentimentsResponse = await fetch("/api/sentiments");
        if (!sentimentsResponse.ok) throw new Error("Failed to fetch sentiments");
        const sentimentsData = await sentimentsResponse.json();

        const sentimentCounts = sentimentsData.sentiments.reduce(
          (acc, sentiment) => {
            if (sentiment.sentiment && sentiment.count) {
              acc[sentiment.sentiment] = parseInt(sentiment.count, 10);
            }
            return acc;
          },
          { positive: 0, neutral: 0, negative: 0 }
        );
        setSentiments(sentimentCounts);

        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // Prepare data for Recharts
  const chartData = [
    { name: "Positive", value: sentiments.positive, color: "#4caf50" },
    { name: "Neutral", value: sentiments.neutral, color: "#ffeb3b" },
    { name: "Negative", value: sentiments.negative, color: "#f44336" },
  ];

  return (
    <main className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-gray-900 via-gray-800 to-black min-h-screen text-white">
      <h1 className="text-4xl font-extrabold mb-8 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 text-transparent bg-clip-text">
        Twitter Sentiment Dashboard
      </h1>

      {/* Loading and Error States */}
      {loading && <p className="text-xl animate-pulse">Loading data...</p>}
      {error && <p className="text-red-500 text-xl">{error}</p>}

      {/* Main Content */}
      {!loading && !error && (
        <>
          {/* Pie Chart */}
          <div className="w-full max-w-md mb-10 bg-gray-800 p-6 rounded-lg shadow-lg">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  fill="#8884d8"
                  label
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend
                  verticalAlign="top"
                  align="center"
                  wrapperStyle={{
                    fontSize: "14px",
                    fontFamily: "Arial, sans-serif",
                    color: "#ffffff",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Tweets Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-6xl">
            {tweets.map((tweet) => (
              <div
                key={tweet.tweet_id}
                className="p-4 border border-gray-700 rounded-lg bg-gradient-to-tl from-gray-800 via-gray-900 to-gray-800 shadow hover:shadow-xl transform hover:scale-105 transition duration-300"
              >
                <Tweet id={tweet.tweet_id} />
                <p className="mt-3 text-gray-300 text-sm">
                  Sentiment:{" "}
                  <strong
                    className={`capitalize ${
                      tweet.sentiment === "positive"
                        ? "text-green-500"
                        : tweet.sentiment === "negative"
                        ? "text-red-500"
                        : "text-yellow-500"
                    }`}
                  >
                    {tweet.sentiment || "Not available"}
                  </strong>
                </p>
              </div>
            ))}
          </div>
        </>
      )}
    </main>
  );
}
