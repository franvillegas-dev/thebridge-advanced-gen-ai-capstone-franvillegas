import { drizzle } from "drizzle-orm/libsql"
import { createClient } from "@libsql/client"
import * as schema from "../drizzle/schema"

const client = createClient({
  url: process.env.DATABASE_URL || "file:./drizzle/data.db",
})

export const db = drizzle(client, { schema })
