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
 * Class: TagPanel
 * Handles tags
 *
 * For convenience, private data member names (both variables and functions) start with an underscore.
 *
 * Dependancies:
 *  <TagWidget> module, <StylePicker> module.
 *  common.js (boxes.permissions, <get_permissions> function)
 *
 * Constructor Parameters:
 *  container - string or DOM object: name of parent DOM block container
 *  options - object: for the moment, only the {canAddTag: <bool>} option is supported (default: true)
 *
 * Signals:
 *  tagPanel:tagDroppedOnZone - signal emitted when a tag has been dropped successfully to a drop zone
 *  tagPanel:tagRemovedFromZone - signal emitted when a tag has been removed successfully from a drop zone
 *  tagPanel:tagDeleted - signal emitted when a tag has been deleted successfully
 *  tagPanel:tagUpdated - signal emitted when a tag has been updated successfully
 *
 */
function TagPanel(container, options) {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * DOM container
	 *
	 */
	var _container = null;
	/*
	 * Var: _options
	 * Hash for options
	 *
	 */
	var _options;
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
	 * Var: _tagsDiv
	 * DOM div displaying available tags
	 *
	 */
	var _tagsDiv = null;
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
	var _tags = $A();
	/*
	 * Var: _dropZone
	 * DOM container acting like a drop zone
	 *
	 */
	var _dropZone = null;
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
	/*
	 * Var: _oldTagData
	 * In tag edition mode, used to store initial tag data (before updates)
	 *
	 */
	var _oldTagData = null;
	/*
	 * Var: _currentTagName
	 * Current tag name being edited
	 *
	 */
	var _currentTagName = null;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------
	

	/*
	 * Function: _showEditForm
	 * Show edition form
	 *
	 */ 
	function _showEditForm(data) {
		if (typeof data == 'undefined') {
			data = $H({
				name: '',
				comment: '',
				style: null
			});
		}
		else
			_oldTagData = data;

		_currentTagName = data.get('name');
		_editDiv.update();
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
		inp = new Element('input', {
			type: 'text', 
			id: _id + 'tag_name_input', 
			maxlength: 15,
			value: data.get('name')
		});
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
		inp = new Element('input', {
			type: 'text', 
			id: _id + 'tag_comment_input',
			value: data.get('comment')
		});
		td.insert(inp);
		tr.insert(td);
		tab.insert(tr);
		var buttd = new Element('td', {colspan: 2}).setStyle({textAlign: 'right'});
		var delb = new Element('input', {type: 'button', value: 'Delete', style: 'margin-right: 10px'});
		delb.observe('click', _deleteTag);
		var upb = new Element('input', {type: 'button', value: 'Update'});
		upb.observe('click', _updateTag);
		
		if (data.get('style')) {
			// Permissions
			tr = new Element('tr');
			td = new Element('td');
			lab = new Element('label').update('Permissions:');
			td.insert(lab);
			tr.insert(td);

			var ptd = new Element('td');
			ptd.insert(get_permissions('tag', _currentTagName, function(resp) {
				if (resp.currentUser.write) {
					delb.show(); upb.show();
				}
				else {
					delb.hide(); upb.hide();
				}
			}));

			tr.insert(ptd);
			tab.insert(tr);

			// Creation date
			tr = new Element('tr');
			td = new Element('td');
			lab = new Element('label').update('Created:');
			td.insert(lab);
			tr.insert(td);

			td = new Element('td').update(data.get('cdate'));
			tr.insert(td);
			tab.insert(tr);
		}

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
		var cancelb = new Element('input', {type: 'button', value: 'Cancel', style: 'margin-right: 10px'});
		cancelb.observe('click', function() {
			_editDiv.slideUp();
			$(_id + 'add_new_span').appear();
		});
		buttd.insert(cancelb);
		buttd.insert(delb).insert(upb);

		if (!data.get('style')) {
			var addb = new Element('input', {type: 'button', value: 'Add'});
			addb.observe('click', _saveTag);
			buttd.insert(addb);
		}

		tr.insert(buttd);
		tab.insert(tr);

		f.insert(tab);
		_editDiv.insert(f);
		if (!_editDiv.visible()) {
			_editDiv.slideDown({
				afterFinish: function() {
					$(_id + 'tag_name_input').focus();
				}
			});
		}
		else
			$(_id + 'tag_name_input').focus();

		if (_previewTag) delete _previewTag;
		_previewTag = new TagWidget(_id + 'preview_td');

		if (_picker) delete _picker;
		_picker = new StylePicker(_id + 'picker_td');
		_previewTag.setStyle(_picker.getStyle());

		if (data.get('style')) {
			_picker.setStyle(data.get('style'));
			_previewTag.setName($(_id + 'tag_name_input').value);
			_previewTag.update();
		}

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
			var inp = $(_id + 'tag_name_input');
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
							log.clear();
							log.msg_error(r.Error);
							return;
						}

						_infoDiv.update();
						_editDiv.slideUp({
							afterFinish: function() {
								log.msg_ok('Tag <b>' + name + '</b> has been added successfully.');
								_infoDiv.fade({
									delay: 1.5,
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
	 * Function: _updateTag
	 * Updates tag to DB
	 *
	 */ 
	function _updateTag() {
		var name = $F(_id + 'tag_name_input').strip();

		if (name.length == 0) {
			alert("Can't update a tag with an empty name!");
			var inp = $(_id + 'tag_name_input');
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
				if (resp.Error) {
					alert('A tag with that name already exists! Please\nchoose another name.');
					$(_id + 'tag_name_input').addClassName('validation_failure');
					$(_id + 'tag_name_input').select();
					console.warn(resp.Error);
					return;
				}

				var log = new Logger(_infoDiv);
				_infoDiv.update();
				_editDiv.slideUp({
					afterFinish: function() {
						log.msg_ok('Tag <b>' + resp.oldname + '</b> has been updated successfully.');
						_infoDiv.fade({
							delay: 1.5,
							afterFinish: function() {
								_checkForTags();
							}
						});
					}
				});

				// Send signal
				document.fire('tagPanel:tagUpdated', {oldname: resp.oldname, name: name, style: _picker.getStyle()});
			}
		);

		var post = {
			// Original name
			NameOrig: _oldTagData.get('name'),
			Name: name,
			Comment: $F(_id + 'tag_comment_input').strip(),
			Style: _picker.getStyle()
		};

		// Send HTTP POST request
		xhr.send('/youpi/tags/update/', $H(post).toQueryString());
	}

	/*
	 * Function: _deleteTag
	 * Deletes tag to DB
	 *
	 */ 
	function _deleteTag() {
		var name = _oldTagData.get('name');
		var r = confirm("Are you sure you want to delete the '" + name + "' tag?");
		if (!r) return;

		var xhr = new HttpRequest(
			null,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				if (resp.Error) {
					console.warn(resp.Error);
					return;
				}

				var log = new Logger(_infoDiv);
				_infoDiv.update();
				_editDiv.slideUp({
					afterFinish: function() {
						log.msg_ok('Tag <b>' + resp.deleted + '</b> has been deleted successfully.');
						_infoDiv.fade({
							delay: 1.5,
							afterFinish: function() {
								_checkForTags();
							}
						});
					}
				});

				// Send signal
				document.fire('tagPanel:tagDeleted', name);
			}
		);

		var post = {
			// Original name
			Name: name
		};

		// Send HTTP POST request
		xhr.send('/youpi/tags/delete/', $H(post).toQueryString());
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

				// Link to add a new tag
				var s = new Element('span', {id: _id + 'add_new_span'}).update('You can ');
				var l = new Element('a', {href: '#'}).update('add a new tag');
				l.observe('click', function() {
					s.fade();
					_showEditForm();
				});
				s.insert(l).insert('.');

				if (!r.tags.length) {
					_infoDiv.update('No tags have been created so far. ');
					if (_options.get('canAddTag')) _infoDiv.insert(s);
					return;
				}

				_infoDiv.appear();
				_infoDiv.update('<b>' + r.tags.length + '</b> tag' + (r.tags.length > 1 ? 's' : '') + ' available.');
				if (_options.get('canAddTag')) _infoDiv.insert(s);
				_tagsDiv.update();

				// Show available tags
				_tags.clear();
				r.tags.each(function(tag) {
					_tags.push(tag);
				});

				_updateTagsZone();
				_tagsDiv.appear();
			}
		);
	
		r.send('/youpi/tags/fetchtags/');
	}

	/*
	 * Function: _updateTagsZone
	 * Clear tags div and fill it with available tags
	 *
	 * Note:
	 *  Provided for convenience since it uses internal <_tags> for rendering
	 *  tags instead of making an AJAX query.
	 *
	 */ 
	function _updateTagsZone() {
		var t;
		_tagsDiv.update();
		_tags.each(function(tag) {
			t = new TagWidget(_tagsDiv, tag.name);
			t.setStyle(tag.style);
			t.setComment(tag.comment);
			t.setOwner(tag.username);
			t.setCreationDate(tag.date);
			t.setEditable(true);
			t.update();
			// Use it _after_ update() call so that Draggable instance
			// can overwrite CSS properties
			t.enableDragNDrop(true);
		});
	}

	/*
	 * Function: setDropZone
	 * Declares a drop zone container to drop tags to
	 *
	 * Parameters:
	 *  zone - DOM or string: container
	 *
	 */ 
	this.setDropZone = function(zone) {
		var zone = $(zone);
		if (!zone) {
			throw "setDropZone: zone must be a DOM container";
			return;
		}

		// Set up drop zones
		if (_dropZone)
			Droppables.remove(_dropZone);

		Droppables.add(zone, {
			containment: _id + 'tags_div',
			hoverclass: 'dropzone_hover',
			onDrop: function(src, dest, event) {
				var found = false;
				zone.select('.tagwidget').each(function(tag, k) {
					if (src.innerHTML == tag.innerHTML) {
						found = true;
					}
				});
				if (found) return;

				// Adds tag to drop zone
				dest.insert(src);
				src.setStyle({left: '5px', top: '0px'});
				dest.highlight();
				_updateTagsZone();

				// Find src object
				var obj;
				_tags.each(function(tag) {
					if (tag.name == src.innerHTML) {
						obj = tag;
						throw $break;
					}
				});

				// Then emit signal
				document.fire('tagPanel:tagDroppedOnZone', obj);
			}
		});

		Droppables.add(_id + 'tags_div', {
			containment: zone,
			hoverclass: 'dropzone_hover',
			onDrop: function(src, dest, event) {
				src.remove();
				dest.highlight();
				_updateTagsZone();

				// Emit signal
				document.fire('tagPanel:tagRemovedFromZone', src.innerHTML);
			}
		});

		_dropZone = zone;
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

		// Options
		_options = $H({canAddTag: true});
		_options.update(options);

		_infoDiv = new Element('div').setStyle({marginTop: '5px'});
		_tagsDiv = new Element('div', {id: _id + 'tags_div'}).setStyle({marginTop: '5px'}).addClassName('tags').hide();
		_editDiv = new Element('div').setStyle({marginTop: '10px'}).hide();
		_container.insert(_tagsDiv).insert(_infoDiv).insert(_editDiv);

		_checkForTags();

		// Custom events
		document.observe('stylePicker:styleChanged', function(event) {
			_previewTag.setStyle(_picker.getStyle());
		});

		document.observe('tagWidget:edit', function(event) {
			// User wants tag edition panel
			_showEditForm(event.memo);
		});
	}

	_render();
}
