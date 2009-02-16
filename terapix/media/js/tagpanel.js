/*
 * Class: TagPanel
 * Handles tags
 *
 * For convenience, private data member names (both variables and functions) start with an underscore.
 *
 * Dependancies:
 *  <TagWidget> module, <StylePicker> module.
 *
 * Constructor Parameters:
 *
 * container - string or DOM object: name of parent DOM block container
 *
 */
function TagPanel(container) {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * DOM container
	 *
	 */
	var _container = null;
	/*
	 * Var: _infoDiv
	 * DOM div displaying info messages
	 *
	 */
	var _infoDiv = null;
	/*
	 * Var: _editDiv
	 * DOM div displaying tag edition form
	 *
	 */
	var _editDiv = null;
	/*
	 * Var: _id
	 * Tag panel id
	 *
	 */
	var _id = 'tag_panel_';


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _tags
	 * Available tags
	 *
	 */
	var _tags = new Array();
	/*
	 * Var: _previewTag
	 * <TagWidget> used for previewing
	 *
	 */
	var _previewTag = null;
	/*
	 * Var: _picker
	 * <StylePicker> used for picking a custom CSS style
	 *
	 */
	var _picker = null;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------
	

	/*
	 * Function: _showEditForm
	 * Show edition form
	 *
	 */ 
	function _showEditForm() {
		var f = new Element('form', {'class': 'tagform'});
		var tab = new Element('table');
		var tr, td, lab, inp;

		// Preview
		tr = new Element('tr');
		td = new Element('td');
		lab = new Element('label').update('Preview:');
		td.insert(lab);
		tr.insert(td);

		td = new Element('td', {id: _id + 'preview_td'});
		tr.insert(td);
		tab.insert(tr);

		// Tag name
		tr = new Element('tr');
		td = new Element('td');
		lab = new Element('label').update('Tag name:');
		td.insert(lab);
		tr.insert(td);

		td = new Element('td');
		inp = new Element('input', {type: 'text', id: _id + 'tag_name_input', maxlength: 15});
		inp.observe('keyup', function() {
			_previewTag.setName(this.value);
			_previewTag.update();
		});
		td.insert(inp);
		tr.insert(td);
		tab.insert(tr);

		// Comment
		tr = new Element('tr');
		td = new Element('td');
		lab = new Element('label').update('Comment:');
		td.insert(lab);
		tr.insert(td);

		td = new Element('td');
		inp = new Element('input', {type: 'text', id: _id + 'tag_comment_input'});
		td.insert(inp);
		tr.insert(td);
		tab.insert(tr);

		// Style
		tr = new Element('tr');
		td = new Element('td');
		lab = new Element('label').update('Style:');
		td.insert(lab);
		tr.insert(td);

		td = new Element('td', {id: _id + 'picker_td'});
		tr.insert(td);
		tab.insert(tr);

		// Buttons
		tr = new Element('tr');
		td = new Element('td', {colspan: 2}).setStyle({textAlign: 'right'});
		var addb = new Element('input', {type: 'button', value: 'Add!'});
		addb.observe('click', function() {
			_saveTag();
		});

		var cancelb = new Element('input', {type: 'button', value: 'Cancel', style: 'margin-right: 10px'});
		cancelb.observe('click', function() {
			_editDiv.slideUp();
			$(_id + 'add_new_span').appear();
		});
		td.insert(cancelb);
		td.insert(addb);
		tr.insert(td);
		tab.insert(tr);

		f.insert(tab);
		_editDiv.insert(f);
		_editDiv.slideDown({
			afterFinish: function() {
				$(_id + 'tag_name_input').focus();
			}
		});

		if (_previewTag) delete _previewTag;
		_previewTag = new TagWidget(_id + 'preview_td');

		if (_picker) delete _picker;
		_picker = new StylePicker(_id + 'picker_td');
		_previewTag.setStyle(_picker.getStyle());

		// Add auto-completion capabilities
		if (_bsn) {
			var options = {
				script: '/youpi/autocompletion/Tag/',
				varname: 'Value',
				json: true,
				maxresults: 20,
				timeout: 2000
			};
			var au = new _bsn.AutoSuggest(_id + 'tag_name_input', options);
		}
	}

	/*
	 * Function: _saveTag
	 * Saves tag to DB
	 *
	 */ 
	function _saveTag() {
		var name = $F(_id + 'tag_name_input').strip();

		if (name.length == 0) {
			alert("Can't save a tag with an empty name!");
			inp.highlight();
			inp.focus();
			return;
		}

		var xhr = new HttpRequest(
			null,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var r = resp.info;
				if (r.name) {
					// Name already exists
					var r = alert("A tag with that name already exists in the database.\nPlease submit another tag name.");
					return;
				}

				// Save to DB
				var s = new HttpRequest(
					null,
					null,
					function(r) {
						var log = new Logger(_infoDiv);
						if (r.Error) {
							log.msg_error(r.Error);
							return;
						}

						_infoDiv.update();
						_editDiv.slideUp({
							afterFinish: function() {
								log.msg_ok('Tag <b>' + name + '</b> has been added successfully.');
								_infoDiv.fade({
									delay: 2.0,
									afterFinish: function() {
										_checkForTags();
									}
								});
							}
						});
					}
				);

				var post = {
					Name: name,
					Comment: $F(_id + 'tag_comment_input').strip(),
					Style: _picker.getStyle()
				};
				s.send('/youpi/tags/save/', $H(post).toQueryString());
			}
		);

		// Send HTTP POST request
		xhr.send('/youpi/tags/info/', 'Name=' + name);
	}

	/*
	 * Function: _checkForTags
	 * Fetches any tag information from DB then updates the UI
	 *
	 */ 
	function _checkForTags() {
		var r = new HttpRequest(
			_infoDiv,
			null,	
			// Custom handler for results
			function(r) {
				_infoDiv.update();
				if (!r.tags.length) {
					_infoDiv.update('No tags have been created so far. ');
					var s = new Element('span', {id: _id + 'add_new_span'}).update('You can ');
					var l = new Element('a', {href: '#'}).update('add a new tag');
					l.observe('click', function() {
						s.fade();
						_editDiv.update();
						_showEditForm();
					});
					s.insert(l).insert('.');
					_infoDiv.insert(s);
					return;
				}

				_infoDiv.appear();
				_infoDiv.update(r.tags.length + ' tag' + (r.tags.length > 1 ? 's' : '') + ' available.');
			}
		);
	
		r.send('/youpi/tags/fetchtags/');
	}

	/*
	 * Function: _render
	 * Main rendering function
	 *
	 */ 
	function _render() {
		_container = $(container);
		if (!container) {
			throw "Please supply a valid DOM container!";
			return;
		}

		_infoDiv = new Element('div');
		_editDiv = new Element('div').setStyle({marginTop: '10px'}).hide();
		_container.insert(_infoDiv).insert(_editDiv);

		_checkForTags();

		document.observe('stylePicker:styleChanged', function(event) {
			_previewTag.setStyle(_picker.getStyle());
		});
	}

	_render();
}
