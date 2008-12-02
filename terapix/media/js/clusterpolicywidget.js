/*
 * Class: ClusterPolicyWidget
 * Cluster policy widget, used in Condor Setup panel to define custom policies
 *
 * File:
 *
 *  clusterpolicywidget.js
 *
 * Dependencies:
 *
 *  common.js - Selects rendering with <getSelect> function; <validate_container> function; <DropdownBox> class.
 *
 * Constructor Parameters:
 *
 * container - string or DOM node: name of parent block container
 * varName - string: global variable name of instance, used internally for public interface definition
 *
 */
function ClusterPolicyWidget(container, varName) {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _instance_name
	 * Name of instance in global namespace
	 *
	 */
	var _instance_name = varName;
	/*
	 * Var: _headerTitle
	 * Header title
	 *
	 */
	var _headerTitle = 'Select all available hosts where';
	/*
	 * Var: _container
	 * Parent DOM container
	 *
	 */ 
	var _container;


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _rowIdx
	 * Current row index in table
	 *
	 */
	var _rowIdx = 0;
	/*
	 * Var: _policyTable
	 * DOM table node
	 *
	 */
	var _policyTable;
	/*
	 * Var: _searchCriteria
	 * Array of strings enumerating search criterias
	 *
	 */
	var _searchCriteria = ['Available memory (RAM)','Available disk space', 'Slots (vms)', 'Host name'];
	/*
	 * Var: _memUnits
	 * Array of strings for memory units
	 *
	 */
	var _memUnits = ['MB', 'GB'];
	/*
	 * Var: _diskUnits
	 * Array of strings for disk units
	 *
	 */
	var _diskUnits = ['MB', 'GB', 'T'];
	/*
	 * Var: _slotsConditions
	 * Array of strings for slots conditions
	 *
	 */
	var _slotsConditions = ['belong to selection', 'are not in selection'];
	/*
	 * Var: _hostConditions
	 * Array of strings for host conditions
	 *
	 */
	var _hostConditions = ['matches', 'does not match'];
	/*
	 * Var: _savePolicyBox
	 * <DropdownBox> for saving current policy
	 *
	 */
	var _savePolicyBox;
	/*
	 * Var: _stringPolicyBox
	 * <DropdownBox> for displaying computed Condor requirement string policy
	 *
	 */
	var _stringPolicyBox;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: _error
	 * Displays custom error message
	 *
	 * Parameters:
	 *  msg - string: error message
	 *
	 */ 
	function _error(msg) {
		alert('ClusterPolicyWidget::' + msg);
	}

	/*
	 * Function: _render
	 * Renders widget
	 *
	 */ 
	function _render() {
		_container.innerHTML = '';
		_container.appendChild(document.createTextNode(_headerTitle));

		_policyTable = document.createElement('table');
		_policyTable.setAttribute('id', _instance_name + '_policy_table');
		_policyTable.setAttribute('class', 'cluster_policy');
		_container.appendChild(_policyTable);

		_addRow();

		// Condor string policy box
		_stringPolicyBox = new DropdownBox(_instance_name + '.getStringPolicyBox()', _container, 'View computed Condor requirement string');
		_stringPolicyBox.setTopLevelContainer(false);
		_stringPolicyBox.setOnClickHandler(function() {
			if (_stringPolicyBox.isOpen())
				_computeCondorRequirementString(_stringPolicyBox.getContentNode());
		} );

		// Save policy box
		_savePolicyBox = new DropdownBox(_instance_name + '.getSavePolicyBox()', _container, 'Save current policy');
		_savePolicyBox.setTopLevelContainer(false);
		_savePolicyBox.setOnClickHandler(function() {
			if (_savePolicyBox.isOpen())
				document.getElementById(_instance_name + '_save_policy_input').focus();
		} );

		var saveDiv = _savePolicyBox.getContentNode();
		var label = document.createElement('label');
		label.appendChild(document.createTextNode('Save as'));
		var iname = document.createElement('input');
		iname.setAttribute('id', _instance_name + '_save_policy_input');
		iname.setAttribute('type', 'text');
		iname.setAttribute('style', 'margin-right: 10px;');
		var ibut = document.createElement('input');
		ibut.setAttribute('type', 'button');
		ibut.setAttribute('value', 'save!');
		saveDiv.appendChild(label);
		saveDiv.appendChild(iname);
		saveDiv.appendChild(ibut);
	}

	/*
	 * Function: getSavePolicyBox
	 * Returns save policy <DropdownBox> instance
	 *
	 * Returns:
	 *  Save policy <DropdownBox> instance
	 *
	 */ 
	this.getSavePolicyBox = function() {
		return _savePolicyBox;
	}

	/*
	 * Function: getStringPolicyBox
	 * Returns Condor requirement string policy <DropdownBox> instance
	 *
	 * Returns:
	 *  Condor requirement string policy <DropdownBox> instance
	 *
	 */ 
	this.getStringPolicyBox = function() {
		return _stringPolicyBox;
	}

	/*
	 * Function: criteriumChanged
	 * Called when search criterium selection has changed
	 *
	 * When selection changes, updates row's content.
	 *
	 * Parameters:
	 *  rowIdx - integer: table row index where the criterium changed
	 *
	 * See Also:
	 *  <_updateRowContent>
	 *
	 */ 
	this.criteriumChanged = function(rowIdx) {
		_updateRowContent(rowIdx);
	}

	/*
	 * Function: _updateRowContent
	 * Updates row's content to match new criterium selection
	 *
	 * Parameters:
	 *  rowIdx - integer: table row index where the criteria changed
	 *
	 * See Also:
	 *  <criteriumChanged>
	 *
	 */ 
	function _updateRowContent(rowIdx) {
		var tr = _getTableTRNode(rowIdx);
		var sel = document.getElementById(_policyTable.id + '_select_' + rowIdx);
		var td = document.getElementById(tr.id + '_condition_td');
		var later = false;
		var prefix;

		removeAllChildrenNodes(td);
		td.innerHTML = '';

		switch (sel.selectedIndex) {
			case 0:
				// Memory
				later = true;
				prefix = 'mem';
				break;

			case 1:
				// Disk space
				later = true;
				prefix = 'disk';
				break;

			case 2:
				// Slots (vms)
				var condSel = getSelect(tr.id + '_' + prefix + '_select', _slotsConditions);
				td.appendChild(condSel);
				var savedSel;
				var r = new HttpRequest(
					null,
					null,	
					function(resp) {
						var sels = resp['Selections'];
						if (!sels.length) {
							savedSel = getSelect('', ['-- no saved selections available --']);
						}
						else {
							savedSel = getSelect('', sels);
						}

						td.appendChild(savedSel);
					}
				);
				r.send('/youpi/profile/getCondorNodeSelections/');
				break;

			case 3:
				// Host name
				var condSel = getSelect(tr.id + '_' + prefix + '_select', _hostConditions);
				var i = document.createElement('input');
				i.setAttribute('id', tr.id + prefix + '_value');
				i.setAttribute('type', 'text');
				td.appendChild(condSel);
				td.appendChild(i);
				break;

			default:
				break;
		}

		if (later) {
			var condSel = getSelect(tr.id + '_' + prefix + '_select', ['>=', '=', '<=']);
			var uSel = getSelect(tr.id + '_unit_select', (sel.selectedIndex == 0 ? _memUnits : _diskUnits));
			var i = document.createElement('input');
			i.setAttribute('id', tr.id + prefix + '_value');
			i.setAttribute('type', 'text');
			i.setAttribute('maxlength', '4');
			i.setAttribute('size', '4');
			td.appendChild(condSel);
			td.appendChild(i);
			td.appendChild(uSel);
		}
	}

	/*
	 * Function: _computeCondorRequirementString
	 * Computes string suitable for Condor requirement parameter
	 *
	 * Parameters:
	 *  container - DOM element container
	 *
	 */ 
	function _computeCondorRequirementString(container) {
		container.innerHTML = '';
		var req_str = '(';
		var trs = _policyTable.getElementsByTagName('tr');
		for (var k=0; k < trs.length; k++) {
			var sel = trs[k].getElementsByTagName('select')[0];
			switch(parseInt(sel.options[sel.selectedIndex].value)) {
				case 0:
					// Memory
					req_str += '&& (Memory) ';
					break;
	
				case 1:
					// Disk space
					req_str += '&& (Disk) ';
					break;
	
				case 2:
					// Slots (vms)
					req_str += '&& (Slots) ';
					break;
	
				case 3:
					// Host name
					req_str += '&& (Hosts) ';
					break;
	
				default:
					break;
			}
		}
		req_str += ')';
		container.appendChild(document.createTextNode(req_str));
	}

	/*
	 * Function: _getTableTRNode
	 * Returns DOM TR node
	 *
	 * Parameters:
	 *  rowIdx - integer: table row index where the criteria changed
	 *
	 * Returns:
	 *  DOM TR node
	 *
	 */ 
	function _getTableTRNode(rowIdx) {
		return document.getElementById(_policyTable.id + '_row_' + rowIdx);
	}

	/*
	 * Function: removeRow
	 * Removes a row from the table
	 *
	 * Parameters:
	 *  rowIdx - integer: table row index where the criteria changed
	 *
	 */ 
	this.removeRow = function(rowIdx) {
		var tr = _getTableTRNode(rowIdx);
		tr.parentNode.removeChild(tr);
	}

	/*
	 * Function: addRow
	 * Adds a new row of data
	 *
	 */ 
	this.addRow = function() {
		_addRow();
	}

	/*
	 * Function: _addRow
	 * Adds a new row of data
	 *
	 */ 
	function _addRow() {
		var tr, td;
		var tab = _policyTable;

		tr = document.createElement('tr');
		tab.appendChild(tr);
		tr.setAttribute('id', tab.id + '_row_' + _rowIdx);

		// - button
		td = document.createElement('td');
		if (_rowIdx > 0) {
			var addb = document.createElement('input');
			addb.setAttribute('type', 'button');
			addb.setAttribute('value', '-');
			addb.setAttribute('onclick', _instance_name + ".removeRow(" + _rowIdx + ");");
			td.appendChild(document.createTextNode('and '));
			td.appendChild(addb);
		}
		tr.appendChild(td);

		// + button
		td = document.createElement('td');
		addb = document.createElement('input');
		addb.setAttribute('type', 'button');
		addb.setAttribute('value', '+');
		addb.setAttribute('onclick', _instance_name + ".addRow();");
		td.appendChild(addb);
		tr.appendChild(td);

		td = document.createElement('td');
		var sel = getSelect(tab.id + '_select_' + _rowIdx, _searchCriteria);
		sel.setAttribute('onchange', _instance_name + ".criteriumChanged(" + _rowIdx + ");");
		td.appendChild(sel);
		tr.appendChild(td);

		// Condition
		td = document.createElement('td');
		td.setAttribute('id', tr.id + '_condition_td');
		tr.appendChild(td);

		_updateRowContent(_rowIdx);
		_rowIdx++;
	}

	/*
	 * Function: _main
	 * Main entry point
	 *
	 */ 
	function _main() {
		_container = validate_container(container);
		if (!_container) {
			_error('_main:: container is not valid!');
			return;
		}

		_render();
	}

	_main();
}
