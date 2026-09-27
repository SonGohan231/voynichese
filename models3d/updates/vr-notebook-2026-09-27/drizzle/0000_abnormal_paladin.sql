CREATE TABLE `vr_notes` (
	`owner` text NOT NULL,
	`id` text NOT NULL,
	`created` text NOT NULL,
	`context` text NOT NULL,
	`transcript` text DEFAULT '' NOT NULL,
	`status` text DEFAULT 'saved' NOT NULL,
	`analysis` text,
	`embedding` text,
	`audio_type` text,
	`has_image` integer DEFAULT 0 NOT NULL,
	`updated` integer NOT NULL,
	`error` text,
	PRIMARY KEY(`owner`, `id`)
);
--> statement-breakpoint
CREATE INDEX `notes_owner_created` ON `vr_notes` (`owner`,`created`);