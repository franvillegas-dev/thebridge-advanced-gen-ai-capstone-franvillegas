import { relations } from "drizzle-orm/relations";
import { projects, calendarEvents, localTasks } from "./schema";

export const calendarEventsRelations = relations(calendarEvents, ({one}) => ({
	project: one(projects, {
		fields: [calendarEvents.projectId],
		references: [projects.id]
	}),
}));

export const projectsRelations = relations(projects, ({many}) => ({
	calendarEvents: many(calendarEvents),
	localTasks: many(localTasks),
}));

export const localTasksRelations = relations(localTasks, ({one}) => ({
	project: one(projects, {
		fields: [localTasks.projectId],
		references: [projects.id]
	}),
}));