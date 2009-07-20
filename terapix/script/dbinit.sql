
INSERT INTO youpi_survey (name) VALUES('CFHTLS'); 
SET @surid = LAST_INSERT_ID();

INSERT INTO youpi_instrument(name) VALUES('STACK');
INSERT INTO youpi_rel_si(survey_id, instrument_id) VALUES(@surid, LAST_INSERT_ID());

INSERT INTO youpi_instrument(name) VALUES('MEGACAM');
INSERT INTO youpi_rel_si(survey_id, instrument_id) VALUES(@surid, LAST_INSERT_ID());

INSERT INTO youpi_instrument(name) VALUES('WIRCAM');
INSERT INTO youpi_rel_si(survey_id, instrument_id) VALUES(@surid, LAST_INSERT_ID());

INSERT INTO youpi_processing_kind(name) VALUES('fitsin');

INSERT INTO youpi_firstqcomment(comment) VALUES ('---'),
		('Poor seeing (>1.2)'),
		('Astrometric keyword problem: some CCDs off'),
		('D3-i rejection'),
		('Galaxy counts below/above expectations'),
		('Some CCDs or half-CCDs missing'),
		('Defocus?'),
		('PSF/Object image doubled'),
		('Diffuse light contamination'),
		('Unusual PSF anisotropy pattern'),
		('Elongated image'),
		('Unusual rh-mag. diagram'),
		('Unusual background image'),
		('Telescope lost guiding?');
