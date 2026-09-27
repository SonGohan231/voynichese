import { sqliteTable, text, integer, primaryKey, index } from 'drizzle-orm/sqlite-core';
export const notes = sqliteTable('vr_notes', {
 owner: text('owner').notNull(), id: text('id').notNull(), created: text('created').notNull(),
 context: text('context').notNull(), transcript: text('transcript').notNull().default(''),
 status: text('status').notNull().default('saved'), analysis: text('analysis'), embedding: text('embedding'),
 audioType: text('audio_type'), hasImage: integer('has_image').notNull().default(0),
 updated: integer('updated').notNull(), error: text('error'),
}, t => [primaryKey({columns:[t.owner,t.id]}), index('notes_owner_created').on(t.owner,t.created)]);
