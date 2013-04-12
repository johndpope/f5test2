{% extends "base.tpl" %}
{% block bvt_active %}active{% endblock %}

{% block title %}BVT Buddy Build{% endblock %}

{% block description %}
     <h2>BVT Buddy Build</h2>
     <p>This is intended for Devs who need to validate user builds (usually before doing a merge). Note that <code>ISO</code> parameter is required. Click on the dotted links to edit values. Check out the console tab for any log messages.</p>
{% endblock %}

{% block options %}
                <table id="options" class="table table-bordered table-striped" style="clear: both">
                    <tbody> 
                        <tr>         
                            <td width="15%">ISO</td>
                            <td width="50%"><a href="#" id="iso" data-bind="editable: inputs.iso" data-type="text" data-inputclass="input-xxlarge" data-placeholder="Required" data-original-title="Enter the path to the ISO file"></a></td>
                            <td width="35%"><span class="muted">e.g. /vol/3/user/harrison/EM-3.2.0.0.0.3.iso</span></td>
                        </tr>

                        <tr>
                            <td>Email</td>
                            <td><a href="#" id="email" data-bind="editable: inputs.email" data-type="text" data-original-title="Enter an email"></a></td>
                            <td><span class="muted">Email recipient to receive test report</span></td>
                        </tr>
                        <tr>         
                            <td>Debug</td>
                            <td><a href="#" id="debug" data-bind="editable: inputs.debug" data-type="checklist" data-value="1" data-original-title="Enable debug?"></a></td>
                            <td><span class="muted">Run in debug mode</span></td>
                        </tr>  
                        <tr data-bind="visible: inputs.debug().length">
                            <td>Tests</td>
                            <td><a href="#" id="tests" data-bind="editable: inputs.tests" data-type="textarea" data-inputclass="input-xxlarge" data-original-title="Enter test files or directories, one per line"></a></td>
                            <td><span class="muted">The path(s) to the test files</span></td>
                        </tr>

                    </tbody>
                </table>
{% endblock %}

{% block js %}
    <script src="/media/app.bvt_deviso.js"></script>
{% endblock %}
