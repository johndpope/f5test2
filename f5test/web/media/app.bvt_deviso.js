$(function(){

    //defaults
    $.fn.editable.defaults.send = 'never'; 
    $.fn.editable.defaults.emptytext = 'Click to edit';
    var default_modules = ['access', 'adc', 'afm', 'asm', 'avr', 'cloud', 'device', 'system', 'platform'];

    //editables
    $('#module').editable({
        inputclass: 'input-large',
        select2: {
           tags: default_modules,
           multiple: true
        }
    });
    $('#ha').editable({
        showbuttons: true,
        emptytext: 'Anything',
        source: [
              {value: 'standalone', text: "Standalone"},
              {value: 'aa', text: "Active-Active"},
              {value: 'pa', text: "Primary-Active"}
        ]
    });

    $('#user .editable').on('hidden', function(e, reason){
         if(reason === 'save' || reason === 'nochange') {
             var $next = $(this).closest('tr').next().find('.editable');
             if($('#autoopen').is(':checked')) {
                 setTimeout(function() {
                     $next.editable('show');
                 }, 300); 
             } else {
                 $next.focus();
             } 
         }
    });

    var MyTask = Task.extend({
    
        // Define the default values for the model's attributes
        defaults: {
        },

        constructor: function(attributes, options){
            this.constructor.__super__.constructor();
        },

        // Attributes
        task_uri: '/bvt/deviso',
        inputs: ko.mapping.fromJS({
          iso: ko.observable().extend({ remote: { type: 'file' }, required: false }),
          hfiso: ko.observable().extend({ remote: { type: 'file' }, required: false }),
          email: ko.observable(),
          //suite: ko.observable("bvt"),
          ha: ko.observableArray([]),
          module: ko.observableArray(default_modules),
          ui: ko.observable(false),
        }),

        // Methods
        /*refresh: function() {
            console.log('refreshed');
        },*/

    });

    var task = new MyTask();
    task.setup_routes();
    ko.applyBindings(task);

});
