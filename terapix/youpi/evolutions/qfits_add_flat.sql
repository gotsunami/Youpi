ALTER TABLE `youpi_plugin_fitsin` ADD COLUMN `exitIfFlatMissing` bool NULL;
UPDATE `youpi_plugin_fitsin` SET `exitIfFlatMissing`=0;
