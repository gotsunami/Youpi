/*
 * Dynamic treeview for pre-ingestion
 *
 */
preIng_treeview = {
	tree : null,
	init_path : '/home/nis/semah',
	behaviour : 'binary_tables',
	name : 'preIng_treeview',
	init : function (host, div_tree) {
		preIng_treeview.host = host;
		// root's JSON branch
		preIng_treeview.root = [
		{
			'id'				: 'root',
			'txt'				: host,
			'img'				: 'base.gif',
			'imgopen'			: 'base.gif',
			'imgclose'			: 'base.gif',
			'canhavechildren'	: true,
		//	'tooltip'			: '<h3>Test</h3>',
			'onopenpopulate' 	: preIng_treeview.branchPopulate,
			'openlink'			: '/spica2/populate/' + preIng_treeview.behaviour + '/' + preIng_treeview.name + preIng_treeview.init_path + '/'
		}
		];

		preIng_treeview.tree = new TafelTree(div_tree, preIng_treeview.root, {
			'generate'			: true,
			'imgBase'			: '/media/js/3rdParty/tafelTree/imgs/',
			'height'			: '200px',
			'defaultImg'		: 'page.gif',
			'defaultImgOpen'	: 'folderopen.gif',
			'defaultImgClose'	: 'folder.gif',
			'onClick'			: preIng_treeview.branchClicked,
			'cookies'			: false} );
	},

	branchPopulate : function (branch, response) {
		//branch.tree.debug(response);
		return response;
	},

	branchClicked : function (branch) {
		var id = branch.getId();

		// Exit if root node or FITS image (leaf)
		if (id == 'root' || !branch.hasChildren())
			return;

		var div_selected_path = document.getElementById('div_selected_path');
		var nb = branch.struct.num_fits_children;
		var b = document.createElement('strong');
		b.appendChild(document.createTextNode(branch.struct.syspath));

		var p = document.createElement('div');

		if (nb > 0) {
			p.setAttribute('class', 'tip');
			p.appendChild(document.createTextNode('OK, the directory '));
			p.appendChild(b);

			p.appendChild(document.createTextNode(' contains ' + branch.struct.num_fits_children 
				+ " FITS tables. You can run the pre-ingestion process by clicking on the 'Run pre-ingestion' button below."));

			document.getElementById("form_submit").setAttribute('style', 'display: block');

			var form = document.getElementById('form_preingestion');

			var hid = document.getElementById('hid_input_path');
			if (hid) {
				form.removeChild(hid);	
			}

			var hid = document.createElement('input');
			hid.setAttribute('id', 'hid_input_path');
			hid.setAttribute('type', 'hidden');
			hid.setAttribute('name', 'path');
			hid.setAttribute('value', branch.struct.syspath);
			form.appendChild(hid);
		}
		else {
			p.setAttribute('class', 'warning');
			p.appendChild(document.createTextNode('The directory '));
			p.appendChild(b);
			p.appendChild(document.createTextNode(' does not contain any FITS tables. Maybe you should look into its subdirectories to find some.'));

			document.getElementById("form_submit").setAttribute('style', 'display: none');
		}
		
		removeAllChildrenNodes(div_selected_path);
		div_selected_path.appendChild(p);
	}
};
