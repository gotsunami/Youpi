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
function force_fitsverify()
{
	var check = $("check_verify");
	var d = $('warn');
	if (check.checked == false) {
		d.setAttribute('style', 'display:block');
		d.setAttribute('width', '50%');
		d.innerHTML = "<p>Fits format integrity could be corrupted<br>This box could be checked to limit <strong>ingestion</strong> problems</p>";
	}
	else {
		d.setAttribute('style', 'display:none');
	}
}

function force_qso_status()
{
	var check = $("check_qso_status");
	var d = $('warn2');
	if (check.checked == false) {
		d.setAttribute('style', 'display:block');
		d.innerHTML = "<p>When QSO status is validated, we ensure that Fits data integrity is relevant for real science issues<br>This box could be checked to limit <strong>processing</strong> problems</p>";
	}
	else {
		d.setAttribute('style', 'display:none');
	}
}

function force_check_allow_several_times()
{
	var check = $("check_allow_several_times");
	var d = $('warn3');
	if (check.checked == false) {
		d.setAttribute('style', 'display:block');
		d.innerHTML="<table><tr><td colspan=\"2\"><p>If <strong>checked</strong>, an image already ingested will be ingested again with a <q><tt class=\"filename\">_#.fits</tt></q> (underscore + number) appended to its db name.<br>For example, <tt class=\"filename\">image.fits</tt> will be renamed to <tt class=\"filename\">image_1.fits</tt> if it has been already ingested.</p><tr><th>Ingestion</th><th>Name</th></tr><tr><td align=\"center\" class=\"number\">1</td><td><tt class=\"filename\">image.fits</tt></td></tr><tr><td align=\"center\" class=\"number\">2</td><td><tt class=\"filename\">image_1.fits</tt></td></tr><tr><td align=\"center\" class=\"number\">...</td></tr><tr><td align=\"center\" class=\"number\">n</td><td><tt class=\"filename\">image_(n-1).fits</tt></td></tr></td></tr></table>";
	}
	else {
		d.setAttribute('style', 'display:none');
	}
}

function ingestionType()
{
	var div_ing = $("ingestion");
	var div_tree = document.createElement('div');
	div_tree.setAttribute('id', 'div_tree');
	div_tree.setAttribute('style', 'width: 400px');
	div_ing.appendChild(div_tree);

	file_browser = new FileBrowser('div_tree', 'file_browser');
	file_browser.setHeaderTitle('Cluster Path Browser');
	file_browser.setRootTitle('Terapix Cluster');
	file_browser.setFilteringPatterns(['*.fits']);
	file_browser.setRootDataPath('/data');
	file_browser.setSubmitButtonHandler(process_form);
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
	var host = path.substr(file_browser.getRootDataPath().length+1);
	host = host.substr(0, host.search('/'));

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

	post = 	'Path=' + path + 
			'&IngestionId=' + ingestionId + '_' + (ingestionPathCurrentIndex+1) + 
			'&ReportEmail=' + $('input_email').value +
			'&CheckSkipVerify=' + ($('check_verify').checked ? 'yes' : 'no') +
			'&CheckQSOStatus=' + ($('check_qso_status').checked  ? 'yes' : 'no') +
			'&CheckAllowSeveralTimes=' + ($('check_allow_several_times').checked  ? 'yes' : 'no') +
			'&Host=' + host;

	// Send HTTP POST request
	xhr.setBusyMsg('Preparing ingestion of ' + path);
	xhr.send('/youpi/ingestion/ingestion2/', post);
}
