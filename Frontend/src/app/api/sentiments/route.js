import { NextResponse } from "next/server";
import { Pool } from "pg";

const pool = new Pool({
  host: "database-1.cjaie6q005ic.us-east-1.rds.amazonaws.com",
  database: "twitter_h1b",
  user: "postgres",
  password: "Jfemihnkrtq123!",
  port: 5432,
  ssl: {
    rejectUnauthorized: false,
  },
});

export async function GET() {
  try {
    const result = await pool.query(
      "SELECT sentiment, COUNT(*) AS count FROM tweets GROUP BY sentiment;"
    );
    return NextResponse.json({ sentiments: result.rows });
  } catch (error) {
    console.error("Error fetching sentiments:", error.message);
    return NextResponse.json({ error: "Failed to fetch sentiment data" }, { status: 500 });
  }
}
