import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core"
import { sql } from "drizzle-orm"

export const projects = sqliteTable("projects", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  name: text("name").notNull(),
  jiraKey: text("jira_key"),
  description: text("description"),
  createdAt: text("created_at").default(sql`(datetime('now'))`),
})

export const localTasks = sqliteTable("local_tasks", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  description: text("description"),
  status: text("status").default("pending"),
  priority: text("priority").default("medium"),
  dueDate: text("due_date"),
  projectId: integer("project_id").references(() => projects.id),
  jiraIssueId: text("jira_issue_id"),
  synced: integer("synced", { mode: "boolean" }).default(false),
  createdAt: text("created_at").default(sql`(datetime('now'))`),
})

export const chatHistory = sqliteTable("chat_history", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  role: text("role").notNull(),
  content: text("content").notNull(),
  createdAt: text("created_at").default(sql`(datetime('now'))`),
})

export const calendarEvents = sqliteTable("calendar_events", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  eventDate: text("event_date").notNull(),
  eventType: text("event_type").notNull(),
  source: text("source").default("local"),
  projectId: integer("project_id").references(() => projects.id),
  createdAt: text("created_at").default(sql`(datetime('now'))`),
})
