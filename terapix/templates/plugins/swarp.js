/*
 * Group: Swarp Plugin
 *
 * JS code for Swarp plugin.
 *
 */
var uid = '{{ plugin.id }}';

var {{ plugin.id }} = {
	/*
	 * Variable: ims
	 * 
	 * <ImageSelector> instance
	 *
	 */
	ims: null,
	/*
	 * Variable: curSelectionIdx
	 * Used by <checkForQFITSData>
	 *
	 */
	curSelectionIdx: 0,
	/*
	 * Variable: weightMissingError
	 * Used by <checkForQFITSData>
	 *
	 */
	weightMissingError: false,
	/*
	 * Function: addSelectionToCart
	 *
	 */
	addSelectionToCart: function() {
		{{ plugin.id }}.curSelectionIdx = 0;
		{{ plugin.id }}.weightMissingError = false;
		sels = {{ plugin.id }}.ims.getListsOfSelections();

		if (!sels) {
			alert('No images selected. Nothing to add to cart !');
			return;
		}

		// Custom output directory
		var output_data_path = '{{ processing_output }}{{ user.username }}/' + uid + '/';
	
		// Set mandatory structures
		var p_data = {	plugin_name : uid, 
						userData : {resultsOutputDir: output_data_path}
		};

		// OPTIONAL
		var wSel = $(uid + '_weights_select');
		var weightPath = '';
		var path = wSel.options[wSel.selectedIndex].text;
		if (path != selector.getNoSelectionPattern()) {
			weightPath = (path == selector.getExtra().title) ? 'QFits-generated weight maps' : path;
		}

		var total = {{ plugin.id }}.ims.getImagesCount();

		// Get config file
		var cSel = $(uid + '_config_name_select');
		var config = cSel.options[cSel.selectedIndex].text;

		// Gets custom output directory
		var custom_dir = $('output_path_input').value.strip().gsub(/\ /, '');
		var output_data_path = '{{ processing_output }}{{ user.username }}/' + uid + '/';

		if (custom_dir)
			output_data_path += custom_dir + '/';

		// Checks that all weight maps are available if EXTRA option has been selected
		var c = $('menuitem_sub_4').update();
		if (path == selector.getExtra().title) {
			menu.activate(4);
			var pre = new Element('pre');
			c.insert(pre);
		
			var log = new Logger(pre);
			log.msg_status('Please note that these tests DO NOT CHECK that WEIGHT files are <b>physically</b> available on disks!');
			log.msg_ok('Found ' + total + ' image' + (total > 1 ? 's' : '') + ' in selection');
			log.msg_status("Using output data path '" + output_data_path + "'");
			log.msg_status("Using '" + config + "' as configuration file");
			log.msg_status('Checking <b>weight maps</b> availability (from QualityFITS)...');
			{{ plugin.id }}.checkForQFITSData(pre, function() {
				{{ plugin.id }}.do_addSelectionToCart({
					useQFITSWeights: 1,
					config: config, 
					imgList: sels, 
					weightPath: weightPath, 
					resultsOutputDir: output_data_path
				});
			});

			return;
		}
		else {
			var msg = new Element('div', {'class': 'tip'}).setStyle({width: '300px'});
			msg.update('Since you have choosen <i>a custom path</i> to WEIGHT data, <b>no additionnal checks are run</b>. ' + 
				'Your item has been directly added to the shopping cart.');
			c.update(msg);
		}

		{{ plugin.id }}.do_addSelectionToCart({
			useQFITSWeights: 0,
			config: config, 
			imgList: sels, 
			weightPath: weightPath, 
			resultsOutputDir: output_data_path
		});
	},

	do_addSelectionToCart: function(data) {
		var total = {{ plugin.id }}.ims.getImagesCount();

		// Add to the shopping cart
		p_data = {	plugin_name	: uid,
					userData 	: data
		};
	
		// Add entry into the shopping cart
		s_cart.addProcessing(	p_data,
								// Custom handler
								function() {
									alert('The current image selection (' + total + ' ' + (total > 1 ? 'images' : 'image') + 
										') has been\nadded to the cart.');
								}
		);
	},

	/*
	 * Function: checkForQFITSData
	 * Check if every images in that selection has associated WEIGHT maps data
	 *
	 * Parameters:
	 *  container - DOM element: DOM block container
	 *  handler - function: custom handler executed once checks are successful
	 *
	 */ 
	checkForQFITSData: function(container, handler) {
		var handler = typeof handler == 'function' ? handler : null;
		var div = new Element('div');
		var log = new Logger(div);
		var sels = {{ plugin.id }}.ims.getListsOfSelections();
		var total = {{ plugin.id }}.ims.getImagesCount();

		var selArr = eval(sels);
		var idList = selArr[{{ plugin.id }}.curSelectionIdx];
	
		div.setStyle({textAlign: 'left'});
		container.insert(div);
	
		var r = new HttpRequest(
				div,
				null,	
				// Custom handler for results
				function(resp) {
					div.update();
					missing = resp.result.missingQFITS;
	
					if (missing.length > 0) {
						log.msg_warning('Missing WEIGHT data for selection ' + ({{ plugin.id }}.curSelectionIdx+1) + 
							' (' + missing.length + ' image' + (missing.length > 1 ? 's' : '') + ' failed!)');
						{{ plugin.id }}.weightMissingError = true;
					}	
					else {
						log.msg_ok('WEIGHT data for selection ' + ({{ plugin.id }}.curSelectionIdx+1) + 
							' (' + idList.length + ' image' + (idList.length > 1 ? 's' : '') + ') is OK');
					}
	
					{{ plugin.id }}.curSelectionIdx++;
	
					if ({{ plugin.id }}.curSelectionIdx < selArr.length) {
						{{ plugin.id }}.checkForQFITSData(container);
					}
					else {
						if ({{ plugin.id }}.weightMissingError) {
							var c = new Element('div').setStyle({paddingLeft: '3px'});
							div.insert(c);
							var wm = new DropdownBox(c, 'View list of images with missing weight maps');
							var pre = new Element('pre').setStyle({
								color: 'brown',
								overflow: 'auto',
								maxHeight: '200px'
							});

							missing.each(function(miss) {
								pre.insert(miss + '<br/>');
							});
							wm.getContentNode().update(pre);

							log.msg_error('Missing WEIGHT information. Selection(s) not added to cart!', true);
							return;
						}

						// All checks are OK. Executes custom handler, if any
						if (handler) handler();
					}
				}
		);
	
		var post = 	'Plugin={{ plugin.id }}&' + 
					'Method=checkForQFITSData&' +
					'IdList=' + idList;
		// Send query
		r.setBusyMsg('Checking selection ' + ({{ plugin.id }}.curSelectionIdx+1) + ' (' + idList.length + ' images)');
		r.send('/youpi/process/plugin/', post);
	},

	/*
	 * Function displayImageCount
	 * Renders list of images to be processed as a summary (used in the shopping cart plugin rendering)
	 *
	 * Parameters:
	 *
	 * imgList - array of arrays of idLists
	 *
	 */
	displayImageCount: function(imgList, container_id) {
		var container = $(container_id);
		var imgList = eval(imgList);
		var c = 0;
		var txt;
		imgList.length > 1 ? txt = 'Batch' : txt = 'Single';
		var selDiv = new Element('div', {'class': 'selectionModeTitle'}).update(txt + ' selection mode:');
		container.insert(selDiv);

		selDiv = new Element('div', {'class': 'listsOfSelections'});

		for (var k=0; k < imgList.length; k++) {
			c = imgList[k].toString().split(',').length;
			if (imgList.length > 1)
				txt = 'Selection ' + (k+1) + ': ' + c + ' image' + (c > 1 ? 's' : '');
			else
				txt = c + ' image' + (c > 1 ? 's' : '');

			selDiv.update(txt);
			selDiv.insert(new Element('br'));
		}
		container.insert(selDiv);
	},

	/*
	 * Function: run
	 * Run processing
	 *
	 * Parameters:
	 *	name - string: name part of ID 
	 *  row - integer: for row number
	 *
	 */ 
	run: function(trid, opts, silent) {
		var silent = typeof silent == 'boolean' ? silent : false;
		var runopts = get_runtime_options(trid);
		var logdiv = $('master_condor_log_div');
	
		var r = new HttpRequest(
				logdiv,
				null,	
				// Custom handler for results
				function(resp) {
					r = resp['result'];
					var success = update_condor_submission_log(resp, silent);
					if (!success) return;
	
					// Silently remove item from the cart
					removeItemFromCart(trid, true);
				}
		);
	
		// Adds various options
		opts = $H(opts);
		opts.set('Plugin', uid);
		opts.set('Method', 'process');
		opts.set('ReprocessValid', (runopts.reprocessValid ? 1 : 0));

		var post = getQueryString(opts) +
			'&' + runopts.clusterPolicy;

		r.send('/youpi/process/plugin/', post);
	},

	reprocessAllFailedProcessings: function(tasksList) {
		alert('TODO...');
	},

	renderOutputDirStats: function(container_id) {
		var container = $(container_id).update();
	
		// global var defined in results.html
		var resp = output_dir_stats_data;
		var stats = resp['Stats'];
	
		var tab = new Element('table', {'class': 'output_dir_stats'});
		var tr,th,td;
		var tr = new Element('tr');
		// Headers
		var headers = $H({	task_success: 'Task success',
							task_failure: 'Task failures',
							task_total: 'Total processings'
		});
		headers.each(function(header) {
			th = new Element('th', {'class': header.key, 'colspan': '2'}).update(header.value);
			tr.insert(th);
		});
		tab.insert(tr);
	
		tr = new Element('tr');
		var val, percent, cls;
		headers.each(function(header, k) {
			switch (k) {
				case 0:
					val = stats['TaskSuccessCount'][0];
					percent = stats['TaskSuccessCount'][1] + '%';
					cls = 'task_success';
					break;
				case 1:
					val = stats['TaskFailureCount'][0];
					percent = stats['TaskFailureCount'][1] + '%';
					cls = 'task_failure';
					break;
				case 2:
					val = stats['Total'];
					percent = '100%';
					cls = 'task_total';
					break;
				default:
					break;
			}
			var td = new Element('td', {'class': cls}).update(val);
			tr.insert(td);

			td = new Element('td', {'class': cls}).update(percent);
			tr.insert(td);
		});
		tab.insert(tr);
		container.insert(tab);
	},

	saveItemForLater: function(trid, opts, silent) {
	//idList, itemId, weightPath, resultsOutputDir, config, silent) {
		opts = $H(opts);
		opts.set('Plugin', uid);
		opts.set('Method', 'saveCartItem');

		var runopts = get_runtime_options(trid);
		var r = new HttpRequest(
				uid + '_result',
				null,	
				// Custom handler for results
				function(resp) {
					// Silently remove item from the cart
					removeItemFromCart(trid, true);
					// Global function (in shoppingcart.html)
					showSavedItems();
				}
		);
	
		var post = getQueryString(opts);
		r.send('/youpi/process/plugin/', post);
	},

	/*
	 * Displays custom result information. 'resp' contains 
	 * server-side info to display
	 *
	 */
	resultsShowEntryDetails: function(container_id) {
		var tr, th, td;
		// See templates/results.html, function showDetails(...)
		var resp = currentReturnedData;
		var container = $(container_id);
		var d = new Element('div', {'class': 'entryResult'});
		var tab = new Element('table', {'class': 'fileBrowser', 'style': 'width: 100%'});
	
		tr = new Element('tr');
		th = new Element('th').update(resp['Title']);
		tr.insert(th);
		tab.insert(tr);
	
		// Duration
		var tdiv = new Element('div', {'class': 'duration'});
		tdiv.insert(resp['Start'] + '<br/>');
		tdiv.insert(resp['End'] + '<br/>');
		var src;
		resp['Success'] ? src = 'success' : src = 'error';
		var img = new Element(	'img', {src: '/media/themes/{{ user.get_profile.guistyle }}/img/admin/icon_' + src + '.gif',
										style: 'padding-right: 5px;'
		});
		tdiv.insert(img);
		tdiv.insert(resp['Duration']);
		tr = new Element('tr');
		td = new Element('td', {style: 'border-bottom: 2px #5b80b2 solid'});
		td.insert(tdiv);
		tr.insert(td);
		tab.insert(tr);
	
		// User
		var udiv = new Element('div', {'class': 'user'});
		udiv.insert('Job initiated by ' + resp['User']);
		udiv.insert(new Element('br'));
		udiv.insert('Exit status: ');
		udiv.insert(new Element('br'));
		var txt;
		resp['Success'] ? txt = 'success' : txt = 'failure';
		var exit_s = new Element('span', {'class': 'exit_' + txt}).update(txt);
		udiv.insert(exit_s);
		td.insert(udiv);
	
		tr = new Element('tr');
		td = new Element('td', {style: 'padding: 0px'});
		var tab2 = new Element('table', {'class': 'qfits-result-entry-params'});
		td.insert(tab2);
		tr.insert(td);
		tab.insert(tr);

		// Thumbnails when successful
		if (resp.Success) {
			tr = new Element('tr', {'class': 'scamp-result-entry-tn'});
			td = new Element('td', {
					onclick: "window.open('" + resp['WWW'] + "swarp.xml');",
					onmouseover: "this.setAttribute('class', 'scamp-result-entry-complete-on');",
					onmouseout: "this.setAttribute('class', 'scamp-result-entry-complete-off');",
					'class': 'scamp-result-entry-complete-off'
			});
			td.update('See Swarp XML file');
			tr.insert(td);
	
			td = new Element('td');
			var tn, imgpath, a;
			resp.Previews.each(function(thumb, k) {
				imgpath = resp.WWW + thumb;
				a = new Element('a', { href: imgpath.replace(/tn_/, ''), rel: 'lightbox[swarp]', title: 'Swarp bitmap of coadded images' });
				tn = new Element('img', {
					src: resp.HasThumbnails ? imgpath : imgpath.replace(/tn_/, ''),
					'class' : 'scamp-result-entry-tn'
				}).hide();
				// Adds a cool fade-in effect
				$(tn).appear({duration: k/3});
	
				if (!resp.HasThumbnails)
					tn.setAttribute('width', '60px');
	
				a.insert(tn);
				td.insert(a);
			});
			tr.insert(td);
			tab2.insert(tr);
		}

		// Processing history
		// Header title
		var hist = resp.History;
		tr = new Element('tr');
		td = new Element('td', { colspan: 2, 'class': 'qfits-result-header-title'});
		td.insert('Swarp processing history (' + hist.length + ')');
		tr.insert(td);
		tab2.insert(tr);

		tr = new Element('tr');
		td = new Element('td', {colspan: '2'});
		htab = new Element('table', {'class': 'qfits-result-history'});
		td.insert(htab);
		tr.insert(td);
		tab2.insert(tr);
	
		hist.each(function(task) {
			tr = new Element('tr');
			// Emphasis of current history entry
			if (resp.TaskId == task.TaskId)
				tr.setAttribute('class', 'history-current');
	
			// Icon
			td = new Element('td');
			var src = task.Success ? 'success' : 'error';
			var img = new Element('img', {src: '/media/themes/{{ user.get_profile.guistyle }}/img/admin/icon_' + src + '.gif'});
			td.insert(img);
			tr.insert(td);
	
			// Date-time, duration
			td = new Element('td');
			var a = new Element('a', {href: '/youpi/results/' + uid + '/' + task.TaskId + '/'});
			a.insert(task.Start + ' (' + task.Duration + ')');
			td.insert(a);
			tr.insert(td);
	
			// Hostname
			tr.insert(new Element('td').update(task.Hostname));
	
			// User
			tr.insert(new Element('td').update(task.User));
	
			// Reprocess option
			td = new Element('td', {'class': 'reprocess'});
			img = new Element('img', {
				onclick: uid + ".reprocess_image('" + task.TaskId + "');",
				src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/reprocess.gif'
			});
			td.insert(img);
			tr.insert(td);
	
			htab.insert(tr);
		});

		// Run parameters
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		td.setAttribute('class', 'qfits-result-header-title');
		td.insert('Swarp run parameters');
		tr.insert(td);
		tab2.insert(tr);

		tr = new Element('tr');
		td = new Element('td');
		td.insert('Input FITS files (' + resp.FITSImages.length + '):');
		tr.insert(td);
	
		td = new Element('td');
		var img_div = new Element('div', {'class': 'min_size'});
		td.insert(img_div);
		resp.FITSImages.each(function(image) {
			img_div.insert(image).insert(new Element('br'));
		});
		tr.insert(td);
		tab2.insert(tr);

		// Weight
		tr = new Element('tr');
		td = new Element('td').insert('Weight path:');
		tr.insert(td);

		td = new Element('td').insert(resp.Weight.length > 0 ? resp.Weight : '--');
		tr.insert(td);
		tab2.insert(tr);

		// Output directory
		tr = new Element('tr');
		td = new Element('td', {nowrap: 'nowrap'}).update('Results output dir:');
		tr.insert(td);
	
		td = new Element('td').update(resp.ResultsOutputDir);
		tr.insert(td);
		tab2.insert(tr);

		// Total exposure time
		tr = new Element('tr');
		td = new Element('td').insert('Exposure time (s):');
		tr.insert(td);

		td = new Element('td').insert(resp.TotalExposureTime);
		tr.insert(td);
		tab2.insert(tr);
	
		// Config file
		tr = new Element('tr');
		td = new Element('td', {colspan: 2});
		if (resp.Success) {
			td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
		}
		var cdiv = new Element('div', {
						id: 'config-' + resp.TaskId,
						'class': 'config_file'
		});
		var pre = new Element('pre').insert(resp.Config);
		cdiv.insert(pre);
		tr.insert(td);
		tab2.insert(tr);

		var confbox = new DropdownBox(td, 'Toggle Swarp config file view');
		$(confbox.getContentNode()).insert(cdiv);
	
		// Error log file when failure
		if (!resp['Success']) {
			tr = new Element('tr');
			td = new Element('td', {style: 'border-bottom: 2px #5b80b2 solid',
									colspan: '2'
			});
			var but = new Element('input', {type: 'button',
											value: 'Toggle error log file view',
											onclick: "toggleDisplay('log-" + resp['TaskId'] + "');"
			});
			td.insert(but);
			var cdiv = new Element('div', { id: 'log-' + resp['TaskId'],
											style: 'height: 200px; overflow: auto; background-color: black; padding-left: 5px; display: none'
			});
			var pre = new Element('pre').update(resp['Log']);
			cdiv.insert(pre);
			td.insert(cdiv);
			tr.insert(td);
			tab2.insert(tr);

			return;
		}
	
		d.insert(tab);
		container.insert(d);
	},

	showSavedItems: function() {
		var cdiv = $('plugin_menuitem_sub_' + uid).update();
		var div = new Element('div', {'class': 'savedItems', id: uid + '_saved_items_div'});
		cdiv.insert(div);
	
		var r = new HttpRequest(
				div.id,
				null,	
				// Custom handler for results
				function(resp) {
					div.update();
	
					var total = resp['result'].length;
					var countNode = $('plugin_' + uid + '_saved_count').update();
					var txt;
					if (total > 0)
						txt = total + ' item' + (total > 1 ? 's' : '');
					else
						txt = 'No item';
					countNode.update(txt);
	
					var table = new Element('table', {'class': 'savedItems'});
					var tr, th;
					var icon = new Element('img', {	'src': '/media/themes/{{ user.get_profile.guistyle }}/img/32x32/' + uid + '.png',
													'style': 'vertical-align:middle; margin-right: 10px;'
					});
	
					tr = new Element('tr');
					th = new Element('th', {'colspan': '8'});
					th.insert(icon);
					th.insert('{{ plugin.description }}: ' + resp['result'].length + ' saved item' + (resp['result'].length > 1 ? 's' : ''));
					tr.insert(th);
					table.insert(tr);
	
					tr = new Element('tr');
					var headers = $A(['Date', 'User', 'Name', '# images', 'Config', 'Paths', 'Action']);
					headers.each(function(header) {
						tr.insert(new Element('th').update(header));
					});
					table.insert(tr);
	
					var delImg, trid;
					var tabi, tabitr, tabitd;
					resp.result.each(function(res, k) {
						idLists = res.idList.evalJSON();
						trid = uid + '_saved_item_' + k + '_tr';
						tr = new Element('tr', {id: trid});

						// Date
						td = new Element('td').update(res.date);
						tr.insert(td);
	
						// User
						td = new Element('td', {'class': 'config'}).update(res.username);
						tr.insert(td);
	
						// Name
						td = new Element('td', {'class': 'name'}).update(res.name);
						tr.insert(td);

						// Images count
						td = new Element('td', {'class': 'imgCount'});
						var sp = new Element('span', {'style': 'font-weight: bold; text-decoration: underline;'});
						sp.update(idLists.length > 1 ? 'Batch' : 'Single');
						td.insert(sp).insert(new Element('br'));

						idLists.each(function(idList) {
							td.insert(idList.length).insert(new Element('br'));
						});
						tr.insert(td);

						// Config
						td = new Element('td', {'class': 'config'}).update(res.config);
						tr.insert(td);

						// Handling paths
						td = new Element('td');
						tabi = new Element('table', {'class': 'info'});
						// Weight
						tabitr = new Element('tr');
						tabitd = new Element('td', {'class': 'label'});
						tabitd.update('Weight: ');
						tabitr.insert(tabitd);
						tabitd = new Element('td', {'class': 'file'});
						if (res.weightPath.length)
							tabitd.update(reduceString(res.weightPath));
						else
							tabitd.update('Not specified');
						tabitr.insert(tabitd);
						tabi.insert(tabitr);
						td.insert(tabi);
						tr.insert(td);
	
						// Delete
						td = new Element('td');
						delImg = new Element('img', {	style: 'margin-right: 5px',
														src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/delete.gif'
						});
						delImg.c_data = {trid: trid, name: res.name};
						delImg.observe('click', function() {
							{{ plugin.id }}.delSavedItem(this.c_data.trid, this.c_data.name);
						});
						td.insert(delImg);

						var addImg = new Element('img', {	src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/addtocart_small.gif'
						});
						addImg.c_data = { 	idList: res.idList,
											config: res.config,
											weightPath: res.weightPath,
											useQFITSWeights: res.useQFITSWeights,
											resultsOutputDir: res.resultsOutputDir
						};
						addImg.observe('click', function() {
							{{ plugin.id }}.addToCart(this.c_data);
						});
						td.insert(addImg);

						tr.insert(td);
						table.insert(tr);
					});

					if (resp.result.length) {
						div.insert(table);
					}
					else {
    	                div.insert(icon);
        	            div.insert('  : no saved item');
					}
				}
		);
	
		var post = 	'Plugin=' + uid + '&Method=getSavedItems';
		r.send('/youpi/process/plugin/', post);
	},

	delSavedItem: function(trid, name) {
		var r = confirm("Are you sure you want to delete saved item '" + name + "'?");
		if (!r) return;
	
		var trNode = $(trid);
		var reload = false;
	
		var r = new HttpRequest(
				uid + '_result',
				null,	
				// Custom handler for results
				function(resp) {
					// 3 = 2 rows of header + 1 row of data
					if (trNode.parentNode.childNodes.length == 3)
						reload = true;
		
					if (reload) 
						window.location.reload();
					else
						trNode.remove();
				}
		);
	
		var post = 	'Plugin=' + uid + '&Method=deleteCartItem&Name=' + name;
		r.send('/youpi/process/plugin/', post);
	},

	addToCart: function(data) {
		var p_data = {	plugin_name : uid,
						userData :	{ 	'config' 			: data.config,
										'imgList' 			: data.idList,
										'weightPath' 		: data.weightPath,
										'resultsOutputDir' 	: data.resultsOutputDir,
										'useQFITSWeights'	: data.useQFITSWeights
						}
		};
	
		s_cart.addProcessing(p_data,
				// Custom hanlder
				function() {
					window.location.reload();
				}
		);
	},

	selectImages: function() {
		var root = document.getElementById('menuitem_sub_0');
		root.setAttribute('align', 'center');
		// Container of the ImageSelector widget
		var div = document.createElement('div');
		div.setAttribute('id', uid + '_results_div');
		div.setAttribute('align', 'center');
		root.appendChild(div);

		{{ plugin.id }}.ims = new ImageSelector(uid + '_results_div');
		{{ plugin.id }}.ims.setTableWidget(new AdvancedTable());
	}
};
