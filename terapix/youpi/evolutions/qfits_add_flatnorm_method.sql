ALTER TABLE `youpi_plugin_fitsin` ADD COLUMN `flatNormMethod` varchar(200) NULL ;
UPDATE `youpi_plugin_fitsin` SET `flatNormMethod`=NULL;
