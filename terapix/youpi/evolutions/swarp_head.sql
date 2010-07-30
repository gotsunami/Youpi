ALTER TABLE `youpi_plugin_swarp` ADD COLUMN `useAutoScampHeads` bool NULL;
ALTER TABLE `youpi_plugin_swarp` DROP COLUMN `useHeadFiles` CASCADE;
UPDATE `youpi_plugin_swarp` SET `useAutoScampHeads` = 1;
