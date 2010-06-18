ALTER TABLE `youpi_plugin_fitsin` ADD COLUMN `exitIfMaskMissing` bool NULL;
UPDATE `youpi_plugin_fitsin` SET `exitIfMaskMissing`=0;
