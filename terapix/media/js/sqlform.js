/*
 * Simulates namespacing. This allows to add several SqlForm instances in one HTML document
 *
 */
var Youpi = {};
Youpi.SQL = {};
Youpi.SQL.currentFormId = 1;

/*
 * Class: SqlForm
 * Generates an HTML form with dynamic capabilities such adding and removing any 
 * number of lines.
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <SqlForm> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * Constructor Parameters:
 *
 * container_id - string: name of parent DOM block container
 * tableName - string: name of SQL table to query
 * varName - string: global variable name of instance, used internally for public interface definition
 * forbiddenFields - array: list of SQL fields that you want to exclude from displaying (they are ignored) 
 *
 * Example:
 *
 * > var myform = new SqlForm('mydiv', 'mytable', 'myform', ['id', 'fk_id']);
 *
 */
function SqlForm(container_id, tableName, varName, forbiddenFields)
{
	// List of table fields that must not be displayed
	var forbFields = forbiddenFields || []
	var container = document.getElementById(container_id);

	// Name of instance if global namespace
	var instance_name = varName;
	var table = tableName;

	var currentRow = 0;
	var cssClass = 'sqlform'

	// Form top node
	var topNode = null;

	var id = 'sqlForm' + Youpi.SQL.currentFormId;
	Youpi.SQL.currentFormId++;
	var debugID = 'debug_' + id;

	// Constant strings
	var caption 	= 'Select';
	var optsANDs 	= ['AND', 'OR'];
	var conditions 	= [	'is equal to', 'is different from', 'contains', 'starts with', 
						'ends with', 'is greater than', 'is lower than' ];
	var limits 		= ['5', '10', '20', '35', '60', '100']; 

	// Looks for table's fields
	// Defines this.tableFields
	var tableFields = [];

	// Main entry point
	fillTableFields();

	this.getTopNode = function() { return topNode; }

	/*
	 * Async call to get list of db fields.
	 * Returns an array.
	 *
	 */
	function fillTableFields() {

		var xhr = new HttpRequest(
			container.id,

			// Custom error handler
			function(msg) {
				var div = document.createElement('div');
				var p = document.createElement('p');

				div.setAttribute('class', 'warning');
				div.setAttribute('style', 'width: 40%');
				p.appendChild(document.createTextNode(msg));
				div.appendChild(p);
				removeAllChildrenNodes(container);
				container.appendChild(div);
			},

			// Custom handler for results
			function(resp) {
				if (forbFields.length == 0) {
					tableFields = resp['fields'];
				}
				else {
					// Forbidden fields supplied
					var res = [];
					for (var i=0; i<resp['fields'].length; i++) {
						var found = false;
						for (var j=0; j<forbFields.length; j++) {
							if (resp['fields'][i] == forbFields[j]) {
								found = true;
								break;
							}
						}
						if (!found) res.push(resp['fields'][i]);
					}
					tableFields = res;
				}

				// Rendering form

				removeAllChildrenNodes(container);
				container.appendChild(render());
			}
		);

		// Send POST request
		xhr.send('/youpi/process/preingestion/tablefields/', 'table=' + table);
	}

	function removeAllChildrenNodes(node)
	{
		// Element ?
		if (node.nodeType != 1)
			return;
	
		if (node.hasChildNodes()) {
			for (var n=0; n < node.childNodes.length; n++) {
				node.removeChild(node.childNodes[n]);
			}
		}
	}

	/*
	 * Builds and returns a DOM select node with a supplied ID and 
	 * and a list of options as parameters
	 *
	 */
	function getSelect(id, options) {
		var select = document.createElement('select');
		select.setAttribute('id', id);
	
		var option = null;
		for(var i=0; i<options.length; i++) {
			option = document.createElement('option');
			option.setAttribute('value', i);
			option.appendChild(document.createTextNode(options[i]));
			select.appendChild(option);
		}
	
		return select;
	}

	/*
	 * Called when the form is submitted. This function is responsible for building a JSON object describing 
	 * the query. It will then be passed to a server-side script with an async call.
	 *
	 */
	this.validate = function() {

		var xhr = new HttpRequest(
			id + 'Result',

			// Custom error handler
			function(msg) {
				document.getElementById(id + 'Result').innerHTML = msg;
			},

			// Custom result handler
			function(resp) {
				var c = document.getElementById(id + 'Result');

				if (resp['data'].length == 0) {
					var div = document.createElement('div');
					var p = document.createElement('p');
	
					div.setAttribute('class', 'warning');
					div.setAttribute('style', 'width: 40%');
					p.appendChild(document.createTextNode('No result found, please try another query.'));
					div.appendChild(p);
					removeAllChildrenNodes(c);
					c.appendChild(div);
					return;
				}

				var t = new ResultTable();
				removeAllChildrenNodes(c);
				c.appendChild(t.render(resp));
			}
		);

		/*
		 * Send HTTP POST request.
		 *
		 * The following code tries to build the query string that will be passed as POST data.
		 *
		 * The post parameters must look like this:
		 * Table=mytable&DisplayField=all&NbLines=&Line0Bool=AND&Line0Field=option&Line0Cond=option&Line0Text=text&...&OrderBy=id&Limit=nb
		 *
		 */
		var selects = topNode.getElementsByTagName('select');
		var df, lines = '';
		// Lines=3,4,7 for example
		var lineNumbers = '';

		for (var i=0; i<selects.length; i++) {
			var sel = selects[i];
			var text = sel.options[sel.selectedIndex].firstChild.nodeValue;

			if (sel.id.search(id + 'DisplaySelect') == 0) {
				df = text;
			}
			else if(sel.id.search(id + 'Select') == 0) {
				var j = sel.id.substr((id + 'Select').length);
				lines += '&Line' + j + 'Field=' + text;
				lineNumbers += j + ',';
			}
			else if(sel.id.search(id + 'CondSelect') == 0) {
				var j = sel.id.substr((id + 'CondSelect').length);
				lines += '&Line' + j + 'Cond=' + text;
				// Get all inputs on current line
				var inputs = sel.parentNode.parentNode.getElementsByTagName('input');
				var val;
				for (var k=0; k<inputs.length; k++) {
					// Replace any '*' wildcard by '%'
					val = inputs[k].value.replace(/%/g, '%25').replace(/\*/g, '%25');
					if(inputs[k].id.search(id + 'Text') == 0) {
						lines += '&Line' + j + 'Text=' + val;
						break;
					}
				}
			}
			else if(sel.id.search(id + 'BoolSelect') == 0) {
				var j = sel.id.substr((id + 'BoolSelect').length);
				lines += '&Line' + j + 'BoolSelect=' + text;
			}
			else if(sel.id.search(id + 'OrderSelect') == 0) {
				var j = sel.id.substr((id + 'OrderSelect').length);
				lines += '&OrderBy=' + text;
			}
			else if(sel.id.search(id + 'LimitSelect') == 0) {
				var j = sel.id.substr((id + 'LimitSelect').length);
				lines += '&Limit=' + text;
			}
		}

		var data = 'Table=' + table + '&DisplayField=' + df + '&Lines=' + lineNumbers.substr(0, lineNumbers.length-1) + lines + '&Hide=' + forbFields.toString();
		xhr.send('/youpi/process/preingestion/query/', data);
	}

	/*
	 * Builds an return a DOM form with a unique ID and dynamic row adding
	 * capabilities
	 *
	 */
	function render() {
		var form, tab, tr, td, but;
	
		topNode = document.createElement('form');
		form = topNode;
	
		form.setAttribute('id', id);
		form.setAttribute('onsubmit', instance_name + '.validate(); return false;');
	
		tab = document.createElement('table');
		tab.setAttribute('class', cssClass);
	
		// First row
		tr = document.createElement('tr');
	
		var selid = genID('DisplaySelect');
		var selNode = getSelect(selid, tableFields);
		var option = document.createElement('option');
		option.setAttribute('style', 'font-weight: bold');
		option.setAttribute('value', '-1');
		option.setAttribute('selected', 'true');
		option.appendChild(document.createTextNode('all'));
		selNode.insertBefore(option, selNode.firstChild);

		td = document.createElement('td');
		td.setAttribute('colspan', '6');
		td.appendChild(document.createTextNode(caption + ' '));
		td.appendChild(selNode);
		td.appendChild(document.createTextNode(' fields where'));

		tr.appendChild(td);
		tab.appendChild(tr);
	
		// Second row
		addTRLine(tr);

		// Order and Limit clauses
		tr = document.createElement('tr');
		td = document.createElement('td');
		td.setAttribute('colspan', '6');
		td.appendChild(document.createTextNode('Order by '));
		td.appendChild(getSelect(genID('OrderSelect'), tableFields));
		td.appendChild(document.createTextNode(' and limit display to '));
		td.appendChild(getSelect(genID('LimitSelect'), limits));
		td.appendChild(document.createTextNode(' results.'));
		tr.appendChild(td);
		tab.appendChild(tr);

		// Submit button
		tr = document.createElement('tr');
		td = document.createElement('td');
		td.setAttribute('colspan', '6');
		td.setAttribute('style', 'text-align: right');
		sub = document.createElement('input');
		sub.setAttribute('type', 'submit');
		sub.setAttribute('value', 'Execute query');
		td.appendChild(sub);
		tr.appendChild(td);
		tab.appendChild(tr);

		form.appendChild(tab);
	
		var err = document.createElement('div');
		err.setAttribute('id', debugID);
		err.setAttribute('class', 'debug');
		form.appendChild(err);

		var result = document.createElement('div');
		result.setAttribute('id', id + 'Result');
		form.appendChild(result);
	
		return form;
	}

	/*
	 * Try to generated a pseudo unique string ID
	 *
	 */
	function genID(name, row) {
		var row = row || currentRow;
		return id + name + row;
	}

	/*
	 * Return a DOM tr node
	 *
	 */
	function addTRLine(after) {
		var tr, td, but;
	
		// DOM node
		after = after || alert('after DOM node not defined !');
	
		// Use a rather unique TR id
		var trid = genID('Line');
		tr = document.createElement('tr');
		tr.setAttribute('id', trid);
	
		// Remove button
		td = document.createElement('td');
		if (currentRow > 0) {
			but = document.createElement('input');
			with (but) {
				var nid = genID('ButtonDel');
				setAttribute('id', nid);
				setAttribute('type', 'button');
				// Try to reach and remove TR DOM element
				setAttribute('onclick', instance_name + ".getTopNode().firstChild.removeChild(document.getElementById('" + nid + "').parentNode.parentNode)");
				setAttribute('value', '-');
			}
			td.appendChild(but);
		}
		tr.appendChild(td);
	
		// Add button
		td = document.createElement('td');
		but = document.createElement('input');
		with (but) {
			var nid = genID('ButtonAdd');
			setAttribute('id', nid);
			setAttribute('type', 'button');
			setAttribute('onclick', instance_name + ".addLine(document.getElementById('" + trid + "'));");
			setAttribute('value', '+');
		}
		td.appendChild(but);
		tr.appendChild(td);
	
		// AND/OR
		td = document.createElement('td');
		if (currentRow > 0) {
			td.appendChild(getSelect(genID('BoolSelect'), optsANDs));
		}
		tr.appendChild(td);
	
		// Fields
		td = document.createElement('td');
		td.appendChild(getSelect(genID('Select'), tableFields));
		tr.appendChild(td);
	
		// Condition
		td = document.createElement('td');
		td.appendChild(getSelect(genID('CondSelect'), conditions));
		tr.appendChild(td);
	
		// Text
		td = document.createElement('td');
		var text = document.createElement('input');
		text.setAttribute('id', genID('Text'));
		text.setAttribute('type', 'text');
		td.appendChild(text);
		tr.appendChild(td);
	
		if (after.nextSibling) {
			after.parentNode.insertBefore(tr, after.nextSibling);
		}
		else {
			after.parentNode.appendChild(tr);
		}
	
		currentRow++;
	}

	/*
	 * Return a DOM tr node
	 * Wrapper for the public interface
	 *
	 */
	this.addLine = function(after) {
		addTRLine(after);
	}
}
