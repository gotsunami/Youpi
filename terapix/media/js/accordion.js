/*
 * Simple code for accordion
 */
var Accordion = Class.create({
	initialize: function(container, opts) {
		this.container = $(container);
		if (this.container == null) {
			throw 'Accordion: bad container name';
			return;
		}
		
		// Options
		this.opts = $H({
			className: {
				toggle: 'vertical_accordion_toggle',
				content: 'vertical_accordion_content'
			},
			direction: 'vertical',
			// On open custom handler
			openHandler: null,
			// Animation duration
			duration: 0.6
		});
		if (typeof opts == 'object') this.opts.update(opts);

		// Animation setup
		this.headers = $$('#' + container + ' .' + this.opts.get('className').toggle);
		this.headers.each(function(node) {
			node.observe('click', function(event) {
				// Open element; 'this' context is bound to the class, so we must use Event#findElement() to retrieve current element
				this._open(event.findElement());
			}.bind(this));
		}.bind(this));
		// Default: hide all content
		$$('.' + this.opts.get('className').content).each(function(e) { e.hide(); });
	},
	// Should be private
	_open: function(node) {
		// Looks for current context container * to get the current element
		var ccontext;
		var toggle_node = node.hasClassName(this.opts.get('className').toggle) ? node : node.up('.' + this.opts.get('className').toggle);
		ccontext = toggle_node.next('.' + this.opts.get('className').content);

		// Close all open panels
		var opens = $$('.' +  this.opts.get('className').content);
		opens.each(function(e) {
			if (e.visible()) {
				e.previous('.' + this.opts.get('className').toggle).removeClassName(this.opts.get('className').toggle + '_active');
				e.slideUp({duration: this.opts.get('duration')});
			}
		}.bind(this));

		// Apply effect on node
		if (this.opts.get('direction') == 'vertical') {
			if (ccontext.visible()) {
				ccontext.slideUp({duration: this.opts.get('duration')});
				ccontext.previous('.' + this.opts.get('className').toggle).removeClassName(this.opts.get('className').toggle + '_active');
			}
			else {
				// Check current index
				var idx;
				this.headers.each(function(n, k) {
					if (n == toggle_node) {
						idx = k;
						throw $break;
					}
				});
				// Call custom handler _before_ sliding
				var handler = this.opts.get('openHandler');
				if (handler && typeof handler == 'function') handler(idx);
				ccontext.slideDown({duration: this.opts.get('duration')});
				ccontext.previous('.' + this.opts.get('className').toggle).addClassName(this.opts.get('className').toggle + '_active');
			}
		}
	},
	_checkPosition: function(idx) {
		if (typeof idx != 'number') {
			throw 'idx must be an integer';
		}
		if (idx > this.headers.length) {
			throw 'idx > length';
		}
	},
	/*
	 * Open a panel
	 *
	 */
	open: function(idx) {
		this._checkPosition(idx);
		this._open(this.headers[idx]);
	},
	/*
	 * Disable a panel
	 *
	 */
	disable: function(idx) {
		this._checkPosition(idx);
		this.headers[idx].addClassName('accordion_disabled');
		this.headers[idx].stopObserving('click');
	},
	/*
	 * Check if a panel is disabled
	 *
	 */
	isDisabled: function(idx) {
		this._checkPosition(idx);
		return this.headers[idx].hasClassName('accordion_disabled');
	},
	/*
	 * Enable a panel
	 *
	 */
	enable: function(idx) {
		if (!this.isDisabled(idx)) return;
		this.headers[idx].removeClassName('accordion_disabled');
		this.headers[idx].observe('click', function(event) {
			// Open element
			this._open(event.findElement());
		}.bind(this));
	}
});
