/*****************************************************************************
 *
 * Copyright (c) 2008-2009 Terapix Youpi development team. All Rights Reserved.
 *                    Mathias Monnerville <monnerville@iap.fr>
 *                    Gregory Semah <semah@iap.fr>
 *
 * This program is Free Software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 *****************************************************************************/

/*
 * Functions related to form and data validation for ingestion process page
 *
 * $Id$
 *
 */

var file_browser;
var runIngestionsClicked = false;
var runIngestionsClickedCount = 0;

/*
 * Action to take when the checkbox related to fitsverify is
 * checked
 *
 */

function force_validation()
{
	var check = $("select_validation");
	var d = $('warn0');
	if (check.options[check.selectedIndex].value == 'no') {
		d.setAttribute('style', 'display:block');
		d.setAttribute('width', '50%');
		d.innerHTML = "<p>Changing this options means that you assume those futures ingested images are not usable for science issues and will be flagged, as <strong>OBSERVED</strong>, in the database.</p>";
	}
	else {
		d.setAttribute('style', 'display:none');
	}
}

function force_fitsverify()
{
	var check = $("check_verify");
	var d = $('warn1');
	if (check.checked == false) {
		d.setAttribute('style', 'display:block');
		d.setAttribute('width', '50%');
		d.innerHTML = "<p>Fits format integrity could be corrupted<br>This box could be checked to limit <strong>ingestion</strong> problems</p>";
	}
	else {
		d.setAttribute('style', 'display:none');
	}
}

function force_check_allow_several_times()
{
	var check = $("check_allow_several_times");
	var d = $('warn2');
	d.setAttribute('style', 'display:block');
	if (check.checked == true) {
		d.innerHTML="<table><tr><td colspan=\"2\"><p>If <strong>checked</strong>, an image already ingested will be ingested again with a <q><tt class=\"filename\">_#.fits</tt></q> (underscore + number) appended to its db name.<br>For example, <tt class=\"filename\">image.fits</tt> will be renamed to <tt class=\"filename\">image_1.fits</tt> if it has been already ingested.</p><tr><th>Ingestion</th><th>Name</th></tr><tr><td align=\"center\" class=\"number\">1</td><td><tt class=\"filename\">image.fits</tt></td></tr><tr><td align=\"center\" class=\"number\">2</td><td><tt class=\"filename\">image_1.fits</tt></td></tr><tr><td align=\"center\" class=\"number\">...</td></tr><tr><td align=\"center\" class=\"number\">n</td><td><tt class=\"filename\">image_(n-1).fits</tt></td></tr></td></tr></table>";
	}
	else {
		d.innerHTML="<p>If <strong>not checked</strong>, an image already ingested will be skipped...</p>";
	}
}

function ingestionType(can_submit_jobs)
{
	var div_ing = $("ingestion");
	var div_tree = document.createElement('div');
	div_tree.setAttribute('id', 'div_tree');
	div_tree.setAttribute('style', 'width: 400px');
	div_ing.appendChild(div_tree);

	file_browser = new FileBrowser('div_tree', 'file_browser');
	file_browser.setHeaderTitle(_fileBrowserSettings.headerTitle);
	file_browser.setRootTitle(_fileBrowserSettings.rootTitle);
	file_browser.setRootDataPath(_fileBrowserSettings.rootDataPath);
	file_browser.setFilteringPatterns(['*.fits']);
	if (can_submit_jobs)
		file_browser.setSubmitButtonHandler(process_form);
	else {
		file_browser.setSubmitButtonHandler(function() {
			alert("You don't have permission to run ingestions on the cluster");
		});
	}
	file_browser.setSelectionMode(file_browser.getSelectionModes().MULTI);
	file_browser.render();
}

/*
 * Encapsulates methods and properties for an input text with
 * email support
 *
 * To use it: 
 *
 * 1. Define an input field:
 * <input id="input_email" type="text" name="report_email" 
 *		onfocus="email_report.onFocus()" 
 *		onblur="email_report.onBlur()" 
 *		onkeyup="email_report.onChange()" size="60"/>
 *
 * 2. Initialize it with
 * email_report.init('input_email');
 *
 */
var email_report = {
	defaultEmailMsg : '<Enter your email address here>',
	styleEnabled : 'font-style:normal;color:black',
	styleDisabled : 'font-style:italic;color:gray',

	init : function(idname) {
		email_report.id = $(idname);
		email_report.id.value = email_report.defaultEmailMsg;
	},

	onBlur : function() {
		id = email_report.id;
		if (id.value == '') {
			id.value = email_report.defaultEmailMsg;
			id.setAttribute('style', email_report.styleDisabled);
		}
	},

	onChange : function() {
		id = email_report.id;
		if (id.value == '') {
			id.value = email_report.defaultEmailMsg;
			id.setAttribute('style', email_report.styleDisabled);
		}
		else
			id.setAttribute('style', email_report.styleEnabled);
	},

	onFocus : function() {
		id = email_report.id;
		if (id.value == email_report.defaultEmailMsg)
			id.value = '';
	}
};


/*
 * Ingestion form validation
 *
 */

function validate_email(fieldname, msg)
{
	var f = $(fieldname);
	if (!f) return;

	with (f) {
		apos = value.indexOf('@');
		dpos = value.indexOf('.');
	}

	if (apos < 1 || (dpos-apos) < 2) {
		alert(msg);
		return false;
	}
	else
		return true;
}

function process_form() {
	var email = $('input_email');
	var ing_id = $('input_ingestion_id');

	if (!validate_email('input_email', 'Please fill in a valid email address to send report to')) {
		email.highlight({ afterFinish: 
			function() { 
				email.focus();
				email.select();
			}
		});
		return false;
	}

	var iid = ing_id.value.strip();
	if (iid.length == 0) {
		alert('Please fill in an ingestion ID (mandatory)!');
		ing_id.focus();
		ing_id.highlight();
		return false;
	}
	else {
		if (runIngestionsClicked) {
			var r = confirm("You have already submitted these ingestions. Are you sure you\nwant to submit them again to the cluster?");
			if (!r) return;
			iid += '.' + runIngestionsClickedCount + '.';
		}

		// Check if it is available for use
		var xhr = new HttpRequest(
			null,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var nb = resp.data.length;
				if (nb > 0) {
					// Do not allow to submit ingestion if ingestion names already exists
					var alike = new Array();
					resp.data.each(function(name) {
						if (new RegExp('^' + iid + '_\\d+').test(name[0]))
							alike.push(name[0]);
					});
					if (alike.length) {
						// ID already exists: not allowed
						alert("This ingestion ID has been already used for ingestion" + (alike.length > 1 ? 's' : '') + '\n' + 
								alike + '\nPlease choose another ingestion ID.');
						ing_id.highlight({ afterFinish: 
							function() { 
								ing_id.focus();
								ing_id.select();
							}
						});
					}
				}
				else  {
					var d = $('cluster_log_div');
					d.innerHTML = '';
					var idv = document.createElement('div');
					idv.appendChild(document.createTextNode('Submitting ingestion jobs to the cluster:'));
					d.appendChild(idv);

					var t = document.createElement('table');
					t.setAttribute('id', 'cluster_log_table');
					var tr, th;
					tr = document.createElement('tr');

					var head = ['Id', 'Job', 'Host', 'Path', ''];
					for (var k=0; k < head.length; k++) {
						th = document.createElement('th');
						th.appendChild(document.createTextNode(head[k]));
						tr.appendChild(th);
					}

					t.appendChild(tr);
					d.appendChild(t);

					// global vars
					runIngestionsClicked = true;
					runIngestionsClickedCount++;

					submitIngestion(iid);
				}
			}
		);

		var post = {
			Table		: 'youpi_ingestion',
			DisplayField: 'label',
			Lines		: 0,
			Line0Field	: 'label',
			Line0Cond	: 'contains',
			Line0Text	: iid + '_%',
			Hide		: '',
			OrderBy		: 'id'
		};

		// Send HTTP POST request
		xhr.send('/youpi/process/preingestion/query/', $H(post).toQueryString());
	}

	return false;
}

var ingestionPathCurrentIndex = 0;
/*
 * Function: submitIngestion
 * Submit one ingestion to cluster
 *
 * Parameters:
 *  ingestionId - string: ingestion Id
 *
 */ 
function submitIngestion(ingestionId) {
	var log = $('cluster_log_div');
	var paths = file_browser.getSelectedDataPaths();
	var path = paths[ingestionPathCurrentIndex][0];

	var tab = $('cluster_log_table');
	var tr, td;
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('colspan', '4');
	td.setAttribute('id', tab.id + '_' + ingestionId + '_tr');
	tr.appendChild(td);
	tab.appendChild(tr);

	var xhr = new HttpRequest(
		td.id,
		// Use default error handler
		null,
		// Custom handler for results
		function(resp) {
			tr.removeChild(td);
			if (resp.Error) {
				var d = new Element('div').addClassName('perm_not_granted').update(resp.Error);
				log.update(d);
				return;
			}

			var fields = ['IngestionId', 'JobId', 'Host', 'Path', ''];
			var img;
			for (var k=0; k < fields.length; k++) {
				td = document.createElement('td');
				td.setAttribute('class', fields[k]);
				if (k == fields.length-1) {
					img = document.createElement('img');
					img.setAttribute('style', 'vertical-align: middle;');
					td.appendChild(img);

					if(resp['Error'].length) {
						icon = 'error';
						var etr = document.createElement('tr');
						var etd = document.createElement('td');
						etd.setAttribute('colspan', '5');
						var div = document.createElement('div');
						div.setAttribute('class', 'error');
						div.appendChild(document.createTextNode('Error: ' + resp['Error']));
						etd.appendChild(div);
						etr.appendChild(etd);
						tab.appendChild(etr);
					}
					else
						icon = 'success';

					img.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/icon_' + icon + '.gif');
				}
				else {
					td.appendChild(document.createTextNode(resp[fields[k]]));
				}
				tr.appendChild(td);
			}
			
			ingestionPathCurrentIndex++;

			if (ingestionPathCurrentIndex < paths.length)
				submitIngestion(ingestionId);
			else
				ingestionPathCurrentIndex = 0;
		}
	);

	var post = 	{
		Path: path,
		IngestionId: ingestionId + '_' + (ingestionPathCurrentIndex+1),
		ReportEmail: $('input_email').value,
		SelectValidationStatus: $('select_validation').options[$('select_validation').selectedIndex].value,
		CheckSkipVerify: $('check_verify').checked ? 'yes' : 'no',
		CheckAllowSeveralTimes: $('check_allow_several_times').checked  ? 'yes' : 'no',
		Itt: $('itt_select').options[$('itt_select').selectedIndex].value	
	}

	// Send HTTP POST request
	xhr.setBusyMsg('Preparing ingestion of ' + path);
	xhr.send('/youpi/ingestion/ingestion2/', $H(post).toQueryString());
}

/*
 * Function: ingestion_history
 * Makes an AJAX query to get ingestion history information
 *
 */ 
function ingestion_history() {
	var sc_accordion = new Accordion('accordion', {
		duration: 0.5,
		clickable: false
	});
	sc_accordion.open(0);

	$('history_count').update('Last ' + $('select_history_limit').value + ' results');
	var tr, td;
	var root = $('ingestion_content');
	var r = new HttpRequest(
		null,
		null,	
		// Custom handler for results
		function(resp) {
			var table = new Element('table', {'class': 'savedItems'});
			tr = new Element('tr');
			var headers = $A(['Status', 'Permissions', 'Options']);
			headers.each(function(header) {
				tr.insert(new Element('th').update(header));
			});
			table.insert(tr);
			resp.data.each(function(entry) {
				tr = new Element('tr');
				// First col
				var actions = new Element('div').setStyle({paddingTop: '4px'});
				// User permissions bundle
				perms = entry.perms.evalJSON(sanitize = true);
				if (perms.currentUser.write) {
					var dela = new Element('a', {'href': '#'}).update('Delete');
					dela.observe('click', function() {
						boxes.confirm("Are you sure you want to delete ingestion <b>" + entry.ID[0] + "</b>?", function() {
							var dr = new HttpRequest(
								null,
								null,	
								function(resp) {
									if (resp.error) {
										var d = $('ilog-' + entry.id);
										d.update();
										var log = new Logger(d);
										log.msg_error(resp.error);
										return;
									}
									// Remove the line
									dela.up('tr').remove();
									Notifier.notify('Ingestion ' + entry.ID[0] + ' has been deleted.');
								}
							);
							dr.send('/youpi/ingestion/delete/' + entry.id + '/');
						}, "Confirm Deletion");
					});
					actions.insert(dela).insert(' - ');
				}
				actions.insert(new Element('a', {'href': entry.log[2], 'target': '_blank'}).update('Log'))
				// Log div
				actions.insert(new Element('div', {'id': 'ilog-' + entry.id}));

				var name = new Element('span', {id: 'ingname-' + entry.id}).update(entry.ID[0]);
				if (perms.currentUser.write) {
					new Ajax.InPlaceEditor(name, '/youpi/ingestion/rename/' + entry.id + '/', {
						okControl: 'link',
						okText: 'save',
						onComplete: function(transport, element) {
							var d = $('ilog-' + entry.id);
							d.update();
							if (transport) {
								var resp = transport.responseText.evalJSON(sanitize = true);
								if (resp.error) {
									element.update(resp.old);
									var log = new Logger(d);
									log.msg_error(resp.error);
								}
							}
							new Effect.Highlight(element, {startcolor: this.options.highlightColor});
						}
					});
				}
				td = new Element('td')
					.addClassName('ing-' + (entry.exit[0] == 0 ? 'success' : 'failure'))
					.update(name)
					.insert(' by ')
					.insert(new Element('i').update(entry.user[0]))
					.insert(' (' + entry.imgcount + ')')
					.insert(' - ' + entry.duration[0])
					.insert(new Element('div').setStyle({paddingTop: '4px'}).insert(entry.start[0]))
					.insert(actions);
				tr.insert(td);
				// Permissions
				td = new Element('td')
					.update(get_permissions_from_data(entry.perms, 'ingestion', entry.id))
					.addClassName('ingestion-perms')
				tr.insert(td);
				// Options
				var opts = new Element('table');
				var otr, otd;
				$A(['fitsverified', 'multiple', 'validated']).each(function(opt) {
					otr = new Element('tr');
					otd = new Element('td').addClassName('ingoptname').setStyle({border: 0}).update(opt);
					otr.insert(otd);
					otd = new Element('td').addClassName('ingopt-' + (entry[opt][0] == 0 ? 'off' : 'on')).setStyle({border: 0});
					otr.insert(otd);
					opts.insert(otr);
				});
				td = new Element('td').update(opts);
				tr.insert(td);
				table.insert(tr);
			});
			root.update(table);
		}
	);
	var post = {limit: $('select_history_limit').value};
	r.send('/youpi/history/ingestion/', $H(post).toQueryString());
}

function updateContent(container, handler) {
	var handler = typeof handler == 'function' ? handler : null;
	var sel = $('itt_select');
	var xhr = new HttpRequest(
		null, // Use default error handler
		null, // Custom handler for results
		function(resp) {
			var data = $H(resp.content);
			var tab = new Element('table').addClassName('itt_table');
			var tr, td;
			data.each(function(pair) {
				if (pair.key == '+COPY') return;
				tr = new Element('tr');
				td = new Element('td').update(pair.key + ';');
				tr.insert(td);
				var vals = $H(pair.value);
				// Second col (mandatory)
				td = new Element('td');
				td.update(vals.get('SRC') + ';');
				tr.insert(td);
				// Third col (optional)
				td = new Element('td');
				td.update(vals.get('MAP'));
				tr.insert(td);
				tab.insert(tr);
			});
			// Add keywords copy at the end of table
			data.each(function(pair) {
				if (pair.key == '+COPY') {
					pair.value.each(function(kw) {
						tr = new Element('tr').addClassName('keyword_copy');
						td = new Element('td').update('+' + kw);
						tr.insert(td);
						td = new Element('td', {colspan: 2}).update('Keyword copy');
						tr.insert(td);
						tab.insert(tr);
					});
				}
			});
			var content = new Element('pre').addClassName('itt_content');
			content.update("--------- Youpi Parameters for the " + resp.instrument + " Instrument ------------").insert(tab);
			container.update(content);
			if (handler) handler();
		}
	);
	var post = { Instrument: sel.options[sel.selectedIndex].value }
	xhr.send('/youpi/ingestion/itt/content/', $H(post).toQueryString());
}
