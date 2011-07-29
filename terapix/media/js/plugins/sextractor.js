/*****************************************************************************
 *
 * Copyright (c) 2008-2011 Terapix Youpi development team. All Rights Reserved.
 *                    Mathias Monnerville <monnerville@iap.fr>
 *                    Gregory Semah <semah@iap.fr>
 *
 * This program is Free Software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 *****************************************************************************/

// JS code for Sextractor plugin

var sex = {
	id: 'sex',
	/*
	 * Variable: ims1
	 *
	 * <ImageSelector> instance
	 *
	 */
	ims1: null,
	ims2: null,
	text_single: "<b> Single Image Mode Option:</b><li>Creation of a catalogue of objects from an astronomic image<br><li>support for WeightMaps<br><li>support for FlagMaps<br>",
	text_dual: "<b>Dual Image Mode Option:</b><li>Image1 is used for detection of sources, image2 for measurements only.<br><li>Image1 and image2 must have the same dimensions.<br><li>For most photometric parameters,image1 will use image2 pixel values, which allows one to easily measurepixel-to-pixel colours.",
	info_dual: "<b> SExtractor is in DUAL IMAGE MODE </b><BR><br>You can specify for each image of this mode :<BR><br><li> A <b>WEIGHT MAP</b><li> A <b>FLAG MAP</b><br><br> Use the path selector to choose:<br><br><li><b>TOP</b> selection for the first image<br><li><b>BOTTOM</b> selection for the image used for measurements",
	paths_loaded: false,

	addSelectionToCart: function() {
		var dualMode = 0;
		var sels, sels1, sels2;
		//Checks for images
		$('single','dual').each( function(id) {
			var chk = id.select('input')[0];
			if(chk.checked) {
				if(chk.value == 'single') {
					sels = this.ims1.getListsOfSelections();
					sels2 = null;
				}
				else {
					dualMode = 1;
					sels1 = this.ims1.getListsOfSelections().evalJSON();
					sels2 = this.ims2.getListsOfSelections().evalJSON();
					sels = '[[' + sels1 + ', ' + sels2 + ']]';
				}
			}
		}.bind(this));

		if (!sels) {
			alert('No images selected. Nothing to add to cart !');
			return;
		}

		// OPTIONAL
		var optPath = new Array();
		var optSel = $(this.id + '_flags_select', this.id + '_weights_select', this.id + '_psf_select', this.id + '_flag_dual_select', this.id + '_weight_dual_select');
		
		optSel.each(function(select, j) {
			if (optSel[j] == null) { 
				return;
			}
			else {
				var path = select.options[select.selectedIndex].text;
				if (path != (selector1.getNoSelectionPattern() || selector2.getNoSelectionPattern())) {
					optPath[j] = path;
				}
			}
		});
		
		var total = this.ims1.getImagesCount();
		
		//Get config file
		var cSel = $(this.id + '_config_name_select');
		var config = cSel.options[cSel.selectedIndex].text;

		//Get parameter file
		var pSel = $(this.id + '_param_name_select');
		var param = pSel.options[pSel.selectedIndex].text;

		//Gets custom output directory
		var output_data_path = $('output_target_path').innerHTML;

		this.do_addSelectionToCart({
			param			: param,
			config			: config, 
			idList			: sels,
			weightPath		: optPath[1] ? optPath[1] : '',
			flagPath		: optPath[0] ? optPath[0] : '',
			psfPath			: optPath[2]  ? optPath[2] : '',
			dualMode		: dualMode,
			dualImage		: sels2 ? sels2 : '',
			dualWeightPath	: optPath[4] ? optPath[4] : '',
			dualFlagPath	: optPath[3] ? optPath[3] : '',
			resultsOutputDir: output_data_path,
		});
	},

	do_addSelectionToCart: function(data) {
		var total = this.ims1.getImagesCount();

		// Finally, add to the processing cart
		p_data = {	plugin_name : this.id , 
					userData 	: data
		};
		s_cart.addProcessing(	p_data,
								// Custom handler
								function() {
									alert('The current image selection (' + total + ' ' + (total > 1 ? 'images' : 'image') + 
										') has been\nadded to the cart.');
								}
		);

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
		
		// Hide action controls
		var tds = $(trid).select('td');
		delImg = tds[0].select('img')[0].hide();
		runDiv = tds[1].select('div.submitItem')[0].hide();
		otherImgs = tds[1].select('img');
		otherImgs.invoke('hide');
	
		var r = new HttpRequest(
				logdiv,
				null,	
				// Custom handler for results
				function(resp) {
					r = resp['result'];
					var success = update_condor_submission_log(resp, silent);
					if (!success) {
						[delImg, runDiv].invoke('show');
						otherImgs.invoke('show');
						return;
					}
					// Silently remove item from the cart
					removeItemFromCart(trid, true);
				}
		);
	
		// Adds various options
		opts = $H(opts);
		opts.set('Plugin', this.id);
		opts.set('Method', 'process');
		opts.set('ReprocessValid', (runopts.reprocessValid ? 1 : 0));
		opts = opts.merge(runopts.clusterPolicy.toQueryParams());

		r.send('/youpi/process/plugin/', opts.toQueryString());
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
		opts = $H(opts);
		opts.set('Plugin', this.id);
		opts.set('Method', 'saveCartItem');

		var runopts = get_runtime_options(trid);
		var r = new HttpRequest(
				this.id + '_result',
				null,	
				// Custom handler for results
				function(resp) {
					// Silently remove item from the cart
					removeItemFromCart(trid, true);
					// Global function (in processingcart.html)
					showSavedItems();
				}
		);
	
		r.send('/youpi/process/plugin/', opts.toQueryString());
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
		if (resp.Error) {
			container.addClassName('perm_not_granted');
			container.update(resp.Error);
			return;
		}
		container.removeClassName('perm_not_granted');

		var d = new Element('div', {'class': 'entryResult'});
		var tab = new Element('table', {'class': 'fileBrowser', 'style': 'width: 100%'});
	
		tr = new Element('tr');

		if (resp['DualMode'] == '1') th = new Element('th').update(resp['Title'] + " (Dual Mode) ");
		else th = new Element('th').update(resp['Title'] + " (Single Mode) ");
		tr.insert(th);
		tab.insert(tr);
	
		// Duration
		var tdiv = new Element('div', {'class': 'duration'});
		tdiv.insert(resp['Start'] + '<br/>');
		tdiv.insert(resp['End'] + '<br/>');
		var src;
		resp['Success'] ? src = 'success' : src = 'error';
		var img = new Element(	'img', {src: '/media/themes/' + guistyle + '/img/admin/icon_' + src + '.gif',
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
					onclick: "window.open('" + resp.WWW + resp.Index + "');",
					onmouseover: "this.setAttribute('class', 'scamp-result-entry-complete-on');",
					onmouseout: "this.setAttribute('class', 'scamp-result-entry-complete-off');",
					'class': 'scamp-result-entry-complete-off'
			});
			td.update('See SEx XML file');
			tr.insert(td);
			td = new Element('td');
			var tn, imgpath, a;
				
			var nb = resp['ResultsOutputDir'].length;

			resp.Previews.each(function(thumb, k) {
				
				thumb = thumb.substring(nb + 1);
				imgpath = resp.WWW + thumb;
				a = new Element('a', { href: imgpath.replace(/tn_/, ''), rel: 'lightbox[sex]', title: 'Sources extracted images' });
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

		// Permissions
		tr = new Element('tr');
		td = new Element('td', {colspan: 2}).setStyle({padding: '0px'});
		td.update(ResultsHelpers.getPermissionsEntry(resp.TaskId));
		tr.insert(td);
		tab2.insert(tr);

		// Condor Job Logs
		tr = new Element('tr');
		td = new Element('td', {colspan: 2}).setStyle({padding: '0px'});
		td.update(ResultsHelpers.getCondorJobLogsEntry(resp.ClusterId, resp.TaskId));
		tr.insert(td);
		tab2.insert(tr);

		// Processing history
		// Header title
		var hist = resp.History;
		tr = new Element('tr');
		td = new Element('td', { colspan: 2, 'class': 'qfits-result-header-title'});
		td.insert('SEx processing history (' + hist.length + ')');
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
			var img = new Element('img', {src: '/media/themes/' + guistyle + '/img/admin/icon_' + src + '.gif'});
			td.insert(img);
			tr.insert(td);
	
			// Date-time, duration
			td = new Element('td');
			var a = new Element('a', {href: '/youpi/results/' + this.id + '/' + task.TaskId + '/'});
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
				onclick: this.id + ".reprocess_image('" + task.TaskId + "');",
				src: '/media/themes/' + guistyle + '/img/misc/reprocess.gif'
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
		td.insert('Sex run parameters');
		tr.insert(td);
		tab2.insert(tr);


		//Flag 
		tr = new Element('tr');
		td = new Element('td').insert('Flag path:');
		tr.insert(td);

		td = new Element('td').insert(resp.Flag.length > 0 ? resp.Flag : '--');
		tr.insert(td);
		tab2.insert(tr);

		// Weight
		tr = new Element('tr');
		td = new Element('td').insert('Weight path:');
		tr.insert(td);

		td = new Element('td').insert(resp.Weight.length > 0 ? resp.Weight : '--');
		tr.insert(td);
		tab2.insert(tr);
	
		// Psf
		tr = new Element('tr');
		td = new Element('td').insert('Psf path:');
		tr.insert(td);

		td = new Element('td').insert(resp.Psf.length > 0 ? resp.Psf : '--');
		tr.insert(td);
		tab2.insert(tr);
	
		//Dual Mode
		tr = new Element('tr');
		td = new Element('td').insert('Image Mode :');
		tr.insert(td);
		
		if (resp.DualMode == '1') {
			td = new Element('td').insert('Dual Mode');
			tr.insert(td);
			tab2.insert(tr);
			//Dual IMage
			tr = new Element('tr');
			td = new Element('td').insert('Dual Image (measurements) :');
			tr.insert(td);

			td = new Element('td').insert(resp.DualImage.length > 0 ? resp.DualImage : '--');
			tr.insert(td);
			tab2.insert(tr);

			//Flag dual
			tr = new Element('tr');
			td = new Element('td').insert('Flag path (Dual Mode):');
			tr.insert(td);

			td = new Element('td').insert(resp.DualFlag.length > 0 ? resp.DualFlag : '--');
			tr.insert(td);
			tab2.insert(tr);

			// Weight dual
			tr = new Element('tr');
			td = new Element('td').insert('Weight path (Dual Mode):');
			tr.insert(td);

			td = new Element('td').insert(resp.DualWeight.length > 0 ? resp.DualWeight : '--');
			tr.insert(td);
			tab2.insert(tr);
		}
		else {

			td = new Element('td').insert('Single Mode');
			tr.insert(td);
			tab2.insert(tr);
		
		}


		// Psf
		tr = new Element('tr');
		td = new Element('td').insert('Psf path:');
		tr.insert(td);

		td = new Element('td').insert(resp.Psf.length > 0 ? resp.Psf : '--');
		tr.insert(td);
		tab2.insert(tr);

		// Output directory
		tr = new Element('tr');
		td = new Element('td', {nowrap: 'nowrap'}).update('Results output dir:');
		tr.insert(td);
	
		td = new Element('td').update(resp.ResultsOutputDir);
		tr.insert(td);
		tab2.insert(tr);
	
		// Config file
		tr = new Element('tr');
		td = new Element('td', {colspan: 2});
		if (resp.Success) {
			td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
		}
		var cdiv1 = new Element('div', {
						id: 'config-' + resp.TaskId,
						'class': 'config_file'
		});
		var pre1 = new Element('pre').insert(resp.Config);
		cdiv1.insert(pre1);
		tr.insert(td);
		tab2.insert(tr);
	
		var configbox = new DropdownBox(td, 'Toggle Sex configuration file view');
		$(configbox.getContentNode()).insert(cdiv1);

		var cdiv2 = new Element('div', {
						id: 'config-' + resp.TaskId,
						'class': 'config_file'
		});

		// param file
		var pre2 = new Element('pre').insert(resp.Param);
		cdiv2.insert(pre2);
		tr.insert(td);
		tab2.insert(tr);
	
		var parambox = new DropdownBox(td, 'Toggle Sex parameters file view');
		$(parambox.getContentNode()).insert(cdiv2);
	
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
		}
	
		d.insert(tab);
		container.insert(d);
	},


	showSavedItems: function() {
		var cdiv = $('plugin_menuitem_sub_' + this.id).update();
		var div = new Element('div', {'class': 'savedItems', id: this.id + '_saved_items_div'});
		cdiv.insert(div);
	
		var r = new HttpRequest(
				div.id,
				null,	
				// Custom handler for results
				function(resp) {
					div.update();
	
					var total = resp['result'].length;
					if (total == 0) {
        	            div.update('No saved item');
						return;
					}
					var table = new Element('table', {'class': 'savedItems'});
					var tr, th;
	
					tr = new Element('tr');
					var headers = $A(['Date', 'Permissions', 'Name', '# images', 'Mode', 'Config','Parameters', 'Paths', 'Action']);
					headers.each(function(header) {
						tr.insert(new Element('th').update(header));
					});
					table.insert(tr);
	
					var delImg, trid;
					var tabi, tabitr, tabitd;
					resp.result.each(function(res, k) {
						idList = eval(res.idList);
						trid = this.id + '_saved_item_' + k + '_tr';
						tr = new Element('tr', {id: trid});
						delImg = new Element('img', {	id: this.id + '_del_saved_item_' + k,
														style: 'margin-right: 5px',
														src: '/media/themes/' + guistyle + '/img/misc/delete.png'
						});

						// Date
						td = new Element('td').update(res.date);
						tr.insert(td);
	
						// Permissions
                        var perms = res.perms.evalJSON(sanitize=true);
						td = new Element('td').addClassName('config').update(get_permissions_from_data(res.perms, 'cartitem', res.itemId));
						tr.insert(td);
	
						// Name
						td = new Element('td', {'class': 'name'}).update(res.name);
						tr.insert(td);
						
						// Images count
						td = new Element('td', {'class': 'imgCount'});
						var sp = new Element('span', {'style': 'font-weight: bold; text-decoration: underline;'});
						if (res.dualMode == 1) {

							sp.update('Single');
							td.insert(sp).insert(new Element('br'));
							tr.insert(td);
							td.insert(idList.length).insert(new Element('br'));
							tr.insert(td);

						}
						else {
							sp.update(res.idList > 1 ? 'Batch' : 'Single');
							td.insert(sp).insert(new Element('br'));
							tr.insert(td);

							idList.each(function(i) {
								td.insert(i.length).insert(new Element('br'));
							});
							tr.insert(td);
						}
	
						//Mode
						td = new Element('td', {'class': 'mode'});
						var spa = new Element('span');
						if (res.dualMode == 1) {
							spa.update('Dual');
							td.insert(spa);
						}
						else {
							spa.update('Single');
							td.insert(spa);
						}

						tr.insert(td);

						// Config
						td = new Element('td', {'class': 'config'}).update(res.config);
						tr.insert(td);

						// Param 
						td = new Element('td', {'class': 'config'}).update(res.param);
						tr.insert(td);

						// Handling paths
						td = new Element('td');
						tabi = new Element('table', {'class': 'info'});
						
						// Flag
						tabitr = new Element('tr');
						tabitd = new Element('td', {'class': 'label'});
						tabitd.update('Flag: ');
						tabitr.insert(tabitd);
						tabitd = new Element('td', {'class': 'file'});
						if (res.flagPath.length)
							tabitd.update(reduceString(res.flagPath));
						else
							tabitd.update('Not specified');
						tabitr.insert(tabitd);
						tabi.insert(tabitr);				
						
						
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
						
						// Psf
						tabitr = new Element('tr');
						tabitd = new Element('td', {'class': 'label'});
						tabitd.update('Psf: ');
						tabitr.insert(tabitd);
						tabitd = new Element('td', {'class': 'file'});
						if (res.psfPath.length)
							tabitd.update(reduceString(res.psfPath));
						else
							tabitd.update('Not specified');
						tabitr.insert(tabitd);
						tabi.insert(tabitr);

						//Weight and Flag for the dual mode
						if (res.dualMode == 1) {
		
							tabitr = new Element('tr');
							tabitd = new Element('td', {'class': 'label'});
							tabitd.update('Weight(dual): ');
							tabitr.insert(tabitd);
							tabitd = new Element('td', {'class': 'file'});
							if (res.dualweightPath.length)
								tabitd.update(reduceString(res.dualweightPath));
							else
								tabitd.update('Not specified');
							tabitr.insert(tabitd);
							tabi.insert(tabitr);				

							tabitr = new Element('tr');
							tabitd = new Element('td', {'class': 'label'});
							tabitd.update('Flag(dual): ');
							tabitr.insert(tabitd);
							tabitd = new Element('td', {'class': 'file'});
							if (res.dualflagPath.length)
								tabitd.update(reduceString(res.dualflagPath));
							else
								tabitd.update('Not specified');
							tabitr.insert(tabitd);
							tabi.insert(tabitr);					

						}

						td.insert(tabi);
						tr.insert(td);
	
						// Delete
						td = new Element('td');
						delImg.c_data = {trid: trid, name: res.name};
						delImg.observe('click', function(c_data) {
							this.delSavedItem(c_data.trid, c_data.name);
						}.bind(this, delImg.c_data));

                        if (perms.currentUser.write)
                            td.insert(delImg);

						//Add to cart
						var addImg = new Element('img', {	src: '/media/themes/' + guistyle + '/img/misc/addtocart_small.png'
						});

						addImg.c_data = {
								 		'idList' 				: res.idList,
										'weightPath'			: res.weightPath,
										'flagPath'				: res.flagPath,
										'psfPath'				: res.psfPath,
										'dualMode'				: res.dualMode,
										'dualImage'				: res.dualImage,
										'dualFlagPath'			: res.dualflagPath,
										'dualWeightPath'		: res.dualweightPath,
										'resultsOutputDir'		: res.resultsOutputDir,
										'config'				: res.config,
										'param'					: res.param,
						};

						addImg.observe('click', function(c_data) {
							this.addToCart(c_data);
						}.bind(this, addImg.c_data));
						td.insert(addImg);

						tr.insert(td);
						table.insert(tr);
					}.bind(this));
					div.insert(table);
				}.bind(this)
		);
	
		var post = 	'Plugin=' + this.id + '&Method=getSavedItems';
		r.send('/youpi/process/plugin/', post);
	},


	delSavedItem: function(trid, name) {
		var r = confirm("Are you sure you want to delete saved item '" + name + "'?");
		if (!r) return;

		var trNode = $(trid);
		var r = new HttpRequest(
				this.id + '_result',
				null,	
				// Custom handler for results
				function(resp) {
					var node = trNode;
					var last = false;
					if (trNode.up('table').select('tr[id]').length == 1) {
						last = true;
						node = trNode.parentNode;
					}
		
					trNode.highlight({
						afterFinish: function() {
							node.fade({
								afterFinish: function() {
									node.remove();
									if (last) eval(this.id + '.showSavedItems()');

									// Notify user
									document.fire('notifier:notify', "Item '" + name + "' successfully deleted");
								}.bind(this)
							});
						}.bind(this)
					});
				}.bind(this)
		);
	
		var post = {
			'Plugin': this.id,
			'Method': 'deleteCartItem',
			'Name'	: name
		};

		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	},

	addToCart: function(data) {
		var p_data = {	plugin_name : this.id,
						userData :	data
		};
		s_cart.addProcessing(p_data,
			// Custom hanlder
			function() {
				window.location.reload();
			}
		);
	},
	/*
	 * Function: getWeightPath
	 * Returns a selector's selected weight path
	 *
	 * Parameters:
	 *	selector - <PathSelectorWidget> instance
	 *	prefix - string: prefix used in addPath()
	 *
	 */ 
	getPath: function(selector, prefix) {
	   return selector.getSelectedPath(selector.getSelectNode(prefix));
	},
	/*
	 * More initialization
	 */
	init: function() {
		var root = $('menuitem_sub_0');
		var root1 = $(this.id + '_results_div');
		var root2 = $(this.id + '_results_div2');
		this.ims1 = new ImageSelector(root1);
		this.ims1.setTableWidget(new AdvancedTable());

		$('selector2_div').hide();
		$('single','dual').each(function (id) {
			id.observe('mouseover', function(event) {
				var el = Event.element(event);
				$('help_mode').show();
				var caption = el.readAttribute('id') == 'single' ? this.text_single : this.text_dual;
				$('help_mode').update(caption);
			}.bind(this));
			id.observe('click', function(event) {
				var el = Event.element(event).up();
				$('help_mode').show();
				$('help_mode').update(eval('this.text_' + el.readAttribute(id)));
				if (el.id == 'dual') {
					$('selector2_div').show();
					if (!this.ims2) {
						this.ims1.getTableWidget().setExclusiveSelectionMode(true);
						this.ims2 = new ImageSelector(root2);
						var at = new AdvancedTable();
						at.setExclusiveSelectionMode(true);
						this.ims2.setTableWidget(at);
					}
					else root2.show();
				}
				else if (el.id == 'single') {
					$('selector2_div').hide();
					if (this.ims2) {
						root2.hide();
						this.ims1.getTableWidget().setExclusiveSelectionMode(false);
					}
				}
			}.bind(this));
		}.bind(this));
		/*
		 * Activates cart mode feature (automatic/manual).
		 * This signal is emitted by the PathSelectorWidget class. Since Sextractor works with 
		 * 2 instances of this class for config and parameter file, the signal is catched twice.
		 * Should be only catched one time.
		 */
		document.observe('PathSelectorWidget:pathsLoaded', function() {
			if (this.paths_loaded) return;
			this.paths_loaded = true;
			cartmode.init(this.id, 
				// Elements to toggle
				[
					$(this.id + '_results_div'), $(this.id + '_results_div2'), 
					$('cartimg'), menu.getEntry(2), $$('table.sex_mode')[0], $('help_mode')
				],
				{}, // No auto params during init, instead provide them later
				// Before handler
				function() {
					// Param config filename
					var pSel = $(this.id + '_param_name_select');
					var param = pSel.options[pSel.selectedIndex].text;

					// Extra params for autoProcessSelection() plugin call (in cartmode.js)
					cartmode.auto_params = {
						Param: param,
						FlagPath: selector1.getPath('flags'), 
						WeightPath: selector1.getPath('weights'),
						PsfPath: selector1.getPath('psf'),
						AddDefaultToCart: $(this.id + '_add_default_to_cart_option').checked ? 0:1,
						// TODO: Dual mode parameters?
						DualMode: 0, // TODO: only supports Single mode for now
						DualImage: '',
						DualWeightPath: '',
						DualFlagPath: ''
					}; 
				}.bind(this),
				// Auto handler
				null,
				// Toggle handler
				function(mode) {
					var e = menu.getEntry(5);
					mode == cartmode.mode.MANUAL ? e.hide() : e.show();
				}
			);
			$('help_mode').hide();

		}.bind(this));
	}
};
