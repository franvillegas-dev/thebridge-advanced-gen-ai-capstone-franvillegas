import { sqliteTable, AnySQLiteColumn, foreignKey, integer, text } from "drizzle-orm/sqlite-core"
  import { sql } from "drizzle-orm"

export const calendarEvents = sqliteTable("calendar_events", {
	id: integer().primaryKey({ autoIncrement: true }).notNull(),
	title: text().notNull(),
	eventDate: text("event_date").notNull(),
	eventType: text("event_type").notNull(),
	source: text().default("local"),
	projectId: integer("project_id").references(() => projects.id),
	createdAt: text("created_at").default("datetime('now')"),
});

export const chatHistory = sqliteTable("chat_history", {
	id: integer().primaryKey({ autoIncrement: true }).notNull(),
	sessionId: text("session_id").notNull(),
	role: text().notNull(),
	content: text().notNull(),
	createdAt: text("created_at").default("datetime('now')"),
});

export const localTasks = sqliteTable("local_tasks", {
	id: integer().primaryKey({ autoIncrement: true }).notNull(),
	title: text().notNull(),
	description: text(),
	status: text().default("pending"),
	priority: text().default("medium"),
	dueDate: text("due_date"),
	projectId: integer("project_id").references(() => projects.id),
	jiraIssueId: text("jira_issue_id"),
	synced: integer().default(false),
	createdAt: text("created_at").default("datetime('now')"),
});

export const projects = sqliteTable("projects", {
	id: integer().primaryKey({ autoIncrement: true }).notNull(),
	name: text().notNull(),
	jiraKey: text("jira_key"),
	description: text(),
	createdAt: text("created_at").default("datetime('now')"),
});

