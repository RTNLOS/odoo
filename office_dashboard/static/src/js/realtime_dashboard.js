/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
$(document).ready(function () {
    var formatCurrency = function(value) {
      if (value) {
            var result = value.toString().replace(/D/, "").replace(/\B(?=(\d{3})+(?!\d))/g, ",")
            if (result == 'undefined' || result == undefined){
              return 0
            }else{
              console.log('NEW CURRENCY DETAILS =>', result);
              return result;
            }

                
            // result = result === 'undefined' ? '0' : result
            // return result// == undefined ? 0 : result 
        }
      return value;
    };
    let currency_name = 'NGN';
     
    let capitalizeText = function(text){
      let txt = ''
      if (text){
        txt = text.charAt(0).toUpperCase() + text.slice(1);
      }
      return txt
    }
    $(window).scroll(function() {
      // Check the scroll position
      if ($(this).scrollTop() === 0) {
        console.log('TOPBAR GOING OFF')
        $('#topbar').fadeOut();
      } else {
        console.log('TOPBAR COMING ON')
        $('#topbar').fadeIn();
      }
    });
    
    var get_object_key = function(object, key){
      result = None
      if (object){
          $.each(object, function(k, v){
              if(k == key){
                result = object[k]
              }
          })
      }
    return result;
    }

    var convert_long_numbers = function(val){
      let formattedNumber = 0.00
      if(val){
        val = String(val)
        console.log('VALUE OF CONVERT ==', typeof(val))
        var inputVal = val.replace(/,/g, '').replace(/(\.\d*)\./g, '$1');
        console.log('VALUE OF CONVERT regex==', inputVal)
        formattedNumber = parseFloat(inputVal).toFixed(2);
      }
      console.log('VALUE OF FORMATED regex==', inputVal)
      return formattedNumber;
      }

    var generate_table_entries = function(table_content, tableId="table_customer_info_id"){
      let total_ng_budget = 0
      let total_ng_revenue = 0
      let total_us_revenue = 0
      let total_us_budget = 0
      $.each(table_content, function (k, val) { 
          total_ng_budget += val.ng_budget_total 
          total_ng_revenue += val.ng_revenue_total 
          total_us_revenue += val.usd_revenue_total 
          total_us_budget += val.usd_budget_total 
          $(`#${tableId}`).append(
            `
            <tr>
              <td class="text-sm">
                <span class="text-xs font-weight-bold">${val.count}</span>
              </td>
              <td class="text-sm">
                <span class="text-xs font-weight-bold">${val.project_name}</span>
              </td>
              <td class="align-middle text-center text-sm">
                <span class="text-xs font-weight-bold">${val.customer_name}</span>
              </td>
              <td class="align-middle text-center text-sm">
                <span class="text-xs font-weight-bold">${val.ng_budget_total}</span>
              </td>
              <td class="align-middle text-center text-sm">
                <span class="text-xs font-weight-bold">${val.total_us_budget}</span>
              </td>
              <td class="align-middle text-center text-sm">
                <span class="text-xs font-weight-bold">${val.ng_revenue_total}</span>
              </td>
              <td class="align-middle text-center text-sm">
                <span class="text-xs font-weight-bold">${val.usd_revenue_total}</span>
              </td> 
               
            </tr> 
          `
          )
      })

      // $('#table_customer_info_id').append(`
      $(`#${tableId}`).append(`
          <tr>
            <div class="mt-5 mb-5">
              <td class="">
                <span class="font-weight-bold"></span>
              </td>
              <td class="">
                <span class="font-weight-bold"></span>
              </td>
              <td class="">
                <span class="font-weight-bold">Grand Total</span>
              </td>

              
              <td class="">
                <span class="font-weight-bold">NGN  ${formatCurrency(total_ng_budget)}</span>
              </td>
              <td class="">
                <span class="font-weight-bold">NGN  ${formatCurrency(total_us_budget)}</span>
              </td>
              <td class="">
                <span class="font-weight-bold">NGN  ${formatCurrency(total_ng_revenue)}</span>
              </td>
              <td class="">
                <span class="font-weight-bold">USD  ${formatCurrency(total_us_revenue)}</span>
              </td>
            </div>
          </tr>
            `);
    }

    var generate_wip_group_table = function(data){
      /**
       {
      'name': 'cfwd', 
      'total':  10,
      'record_ids': [1,3,56]
      }
       */
      let total = 0
      let tbody_wip_group = 'tbody_wip_group'
      $("#tbody_wip_group").empty();
      $.each(data, function (key, val) {
        console.log('DID I REACH HERE ', val)
        console.log('WHAT IS TBODY ', $(`#${tbody_wip_group}`))
        $(`#${tbody_wip_group}`).append(
          `<tr>
              <td class="bg-light p-2">${capitalizeText(val.name)}</td>
              <td class="p-1 clickcard" value="[${val.record_ids}]">${val.total}</td>
          </tr>`
      )
      total += parseInt(val.total)

    })

    $(`#${tbody_wip_group}`).append(
        `<tr>
              <td class="bg-light p-2"><strong>Total</strong></td>
              <td class="bg-light p-1"><strong>${total}</strong></td>
          </tr>`
      )
    }

    var generate_wip_table = function(total_wip_body, table_content, grandTotalRow){
      // hide other groups and leave only WIPtable div
      // clear the wip tbodys at every render
      $(`#${total_wip_body}`).empty();
      var curr_symbol = currency_name == 'NGN' ? '₦' : '$'
      console.log("Displaying wip table", table_content)
      $('#generalOverviewCard').addClass('d-none');
      $('#fileAdminDiv').addClass('d-none');
      $('#mmrTableDiv').addClass('d-none');
      $('#frameAgreementDiv').addClass('d-none');
      $('#wipTableDiv').removeClass('d-none');
      $.each(table_content, function (key, val) {
        console.log("trending key", key)
        console.log("trending val", val)
        // {
        //   'agency':{
        //       'name': 'Agency', 
        //       'wip_revenue': 10000, 
        //       'wip_cost': 10000, 
        //       'margin': 10000
        //       },
        //  'cfwd':{
        //       'name': 'cfwd', 
        //       'wip_revenue': 10000, 
        //       'wip_cost': 10000, 
        //       'margin': 10000
        //       },
        //   }
        $(`#${total_wip_body}`).append(
            `
            <tr>
                <td class="bg-light p-2">${capitalizeText(val.name)}</td>
                <td class="p-1">${curr_symbol}${formatCurrency(convert_long_numbers(val.wip_revenue))}</td>
                <td class="p-1">${curr_symbol}${formatCurrency(convert_long_numbers(val.wip_cost))}</td>
                <td class="p-1">${curr_symbol}${formatCurrency(convert_long_numbers(val.margin))}</td>
            </tr>
            `
        )
      })
      $(`#${total_wip_body}`).append(
        `
          <tr>
              <td class="bg-light p-2"><strong>${capitalizeText(grandTotalRow.name)}</strong></td>
              <td class="bg-light p-1"><strong>${curr_symbol}${formatCurrency(convert_long_numbers(grandTotalRow.wip_revenue))}</strong></td>
              <td class="bg-light p-1"><strong>${curr_symbol}${formatCurrency(convert_long_numbers(grandTotalRow.wip_cost))}</strong></td>
              <td class="bg-light p-1"><strong>${curr_symbol}${formatCurrency(convert_long_numbers(grandTotalRow.margin))}</strong></td>
          </tr>
          `
      )
      
    }

    var generate_realtime_charts = function(
      x_axis, y_axis, canvasId, chartType, displayLabel, other_properties=null){
      var chartObject = document.getElementById(canvasId).getContext("2d");
      // xa = x_axis.length
      // ya = y_axis.length
      if(x_axis !== '[]' || y_axis !== '[]'){
        console.log(`${x_axis} and ${y_axis}`)
        new Chart(chartObject, {
            type: chartType,
            data: {
              labels: x_axis || [NaN],
              datasets: [{
                  label: displayLabel,
                  data: y_axis || [10],
                  borderWidth: other_properties['borderWidth'],
                  backgroundColor: other_properties['backgroundColor'],
                  borderRadius: other_properties['borderRadius'],
                  borderSkipped: other_properties['borderSkipped'],
                  maxBarThickness: other_properties['maxBarThickness'],
                  hoverBorderColor: other_properties['hoverBorderColor'],
                  tension: other_properties['tension']
                }],
              },
            options: other_properties['options'] 
          });
      }else{
        console.log("No matching length of items to display")
      }
    };

    var generate_frame_agreement_chart = function(data){
      // guageChartCanvas
      let existingChart = Chart.getChart("guageChartCanvas");
      if (existingChart != undefined){
          existingChart.destroy();
      }
      var guageChart = document.getElementById("guageChartCanvas").getContext("2d");
      new Chart(guageChart, {
          type: 'doughnut',
          data: {
            labels: data.frame_agreement_x,
            datasets: [{
              label: '# of',
              data: data.frame_agreement_y,
              borderWidth: 1,
              rotation: 270,
              circumference: 180,
              cutout: '80%', 
              backgroundColor: [
                // 'rgb(253, 241, 5)', //yellow
                'rgb(16, 235, 4)',
                'rgba(232, 5, 43, 0.839)',
              
              // 'rgba(175, 207, 87, 0.89)', 
              ]
            }]
          },
          options: {
            scales: {
              y: {
                beginAtZero: true
              }
            },
            aspectRatio: 1.5,
            plugins: {
              legend: {
                  display: false
              }
            }
          }
        });
      var budget_text = data.frame_agreement_budget // data.frame_agreement_y.length > 0 ? data.frame_agreement_y[0] : '';
      var currency_symbol = data.currency_symbol;
      $('#fr_budget_text').text(`${currency_symbol} ${formatCurrency(budget_text)}`);
      $('#fr_invoice_text').text(`${currency_symbol} ${formatCurrency(data.confirmed_so)}`);
      $('#budget_percentage').text(formatCurrency(data.frame_agreement_y[1]));
      $('#invoice_percentage').text(formatCurrency(data.frame_agreement_y[0]));

      
    }

    // GraphDynamicDisplay(mainx_axis, mainy_axis, "donut-chart", "doughnut");
    PublicWidget.registry.realTime = PublicWidget.Widget.extend({
        selector: '#office-dashboard-content',
        start: function(){
            var self = this;
            return this._super.apply(this, arguments).then(function(){
                console.log("real time dashboard loading");
            });

        },
        willStart: function(){
            var self = this; 
            return this._super.apply(this, arguments).then(function(){
                console.log("real time dashboard  2"); 
            })
        },
        events: {
            'change .USD': function(ev){
              let usd = $('#USD');
              if (usd.prop('checked')){
                // console.log('Checked');
                currency_name = "USD";
                console.log('Checked -- ', currency_name);
                $('#NGN').prop('checked', false);
              }
            },
            'change .NGN': function(ev){
              // let ev = $(ev.target);
              let ngn = $('#NGN');
              if (ngn.prop('checked')){
                currency_name = "NGN";
                console.log('Checked -- ', currency_name);
                $('#USD').prop('checked', false);
              }
            },
          
            'click .clickApply': async function(ev){
                let qty_elm = $(ev.target);
                let y_data_for_chart = $('#y_data_for_chart');
                let x_data_for_chart = $('#x_data_for_chart');
                let line_doughnut_filter = $('#line_doughnut_filter')//.text('');
                let to_be_invoiced = $('#to_be_invoiced');
                let to_be_closed_invoiced = $('#to_be_closed_invoiced');
                let output_opened_files = $('#output_opened_files');
                let closed_invoiced = $('#closed_invoiced'); 
                let total_budget = $('#total_budget'); 
                let total_invoiced_revenue = $('#total_invoiced_revenue'); 
                let total_paid_invoiced_revenue = $('#total_paid_invoiced_revenue'); 
                let total_revenue_balance = $('#total_revenue_balance'); 
                let balance_budget_cost = $('#balance_budget_cost'); 
                let doughnutCanvas = $('#doughnutCanvasDiv'); 
                let chartBars = $('#chartbarsDiv'); 
                let tickchartLine = $('#tickchartlineDiv'); 
                let LineChartDiv = $('#LineChartDiv'); 
                let table_customer_info_id = $('#table_customer_info_id'); 
                let mmr_table_customer_info_id = $('#mmr_table_customer_info_id'); 

                // Empty the already populated values
                y_data_for_chart.text('0');
                x_data_for_chart.text('0');
                line_doughnut_filter.text('0');
                to_be_invoiced.text('0');
                to_be_closed_invoiced.text('0');
                output_opened_files.text('0');
                total_budget.text('0');
                closed_invoiced.text('0');
                total_invoiced_revenue.text('0');
                total_paid_invoiced_revenue.text('0');
                total_revenue_balance.text('0');
                balance_budget_cost.text('0');

                //charts empty
                LineChartDiv.empty();
                doughnutCanvas.empty();
                chartBars.empty();
                tickchartLine.empty();
                table_customer_info_id.empty();
                mmr_table_customer_info_id.empty();
                // empty ended
                document.getElementById("mysidebar").style.width = "0px";
                $.blockUI({
                    'message': '<h2 class="card-name">Please wait ...</h2>'
                });

                // fetch data
                await jsonrpc('/refresh-data', {
                  project: $('#memoProjectFilter').val(),
                  project_file_type: $('#memoProjectFilter').val(),
                  project_file_category_type: $('#memoProjecttypeFilter').val(),
                  customer_name: $('#memoCustomerFilter').val(),
                  currency_name: currency_name,
                  code: $('#searchdashboard_val').val(),
                  // date_from: $('#date_from'),
                  // date_to: $('#date_to'),
                  year: $('#memoYearFilter').val(),
                  branch: $('#memoBranchFilter').val(),
                  month: $('#memoMonthFilter').val(),
                  frame_agreement_id: $('#memoFRFilter').val(),
                  is_json: 'yes',
                  
                }).then(function(data){
                    console.log('test realtime data upcoming', data)
                    y_data_for_chart.text(JSON.parse(data.y_data_chart).data)
                    x_data_for_chart.text(JSON.parse(data.x_data_chart).data)
                    // line_doughnut_filter.text(JSON.parse(data.line_doughnut_filter).data)
                    output_opened_files.text(data.output_opened_files.count);
                    // output_opened_files.val(data.output_opened_files.records);
                    output_opened_files.attr('value', data.output_opened_files.records)
                    to_be_invoiced.text(data.to_be_invoiced.count);
                    console.log('what is invoice val', data.to_be_invoiced.records)
                    console.log('what is invoice count', data.to_be_invoiced.count)
                    to_be_invoiced.val(data.to_be_invoiced.records);
                    to_be_invoiced.attr('value', data.to_be_invoiced.records)

                    to_be_closed_invoiced.text(data.to_be_closed_invoiced.count);
                    to_be_closed_invoiced.val(data.to_be_closed_invoiced.records);
                    to_be_closed_invoiced.attr('value', data.to_be_closed_invoiced.records)

                    closed_invoiced.text(data.closed_invoiced.count);
                    closed_invoiced.val(data.closed_invoiced.records);
                    closed_invoiced.attr('value', data.closed_invoiced.records)

                    $('#budget_revenue_total').text(formatCurrency(data.budget_revenue_total))
                    $('#booked_budget_cost').text(formatCurrency(data.booked_budget_cost))
                    $('#paid_budget_cost').text(formatCurrency(data.paid_budget_cost))
                    $('#balance_budget_cost').text(formatCurrency(data.balance_budget_cost))

                    total_invoiced_revenue.text(formatCurrency(data.total_invoiced_revenue));
                    total_budget.text(formatCurrency(data.total_budget));
                    // total_budget.text(data.total_budget);
                    total_paid_invoiced_revenue.text(formatCurrency(data.total_paid_invoiced_revenue));
                    total_revenue_balance.text(formatCurrency(data.total_revenue_balance));
                    // total_paid_invoiced_revenue.text(data.total_paid_invoiced_revenue);

                    var project_type_name = JSON.parse(data.line_doughnut_filter).project_type_name
                    var project_budget = JSON.parse(data.line_doughnut_filter).project_budget
                    var project_revenue = JSON.parse(data.line_doughnut_filter).project_revenue
                    var month_label = JSON.parse(data.line_doughnut_filter).month_label 
                    var month_sales_amount = JSON.parse(data.line_doughnut_filter).month_sales_amount 
                    var project_counter_item = JSON.parse(data.line_doughnut_filter).project_counter_item 
                    var project_counter = JSON.parse(data.line_doughnut_filter).project_counter 
                    // var group_project_table = JSON.parse(data.group_project_table) // list of object [{}]
                    var group_project_table = data.group_project_table 
                    var dynamicMMRTable = data.grp_mmr_data 

                    // var wipTotalData = JSON.parse(data.wipTotalData).data // [{'name': 'Agency', 'wip_revenue': 10000, 'wip_cost': 10000, 'margin': 10000}, ...] 
                    var wipTotalData = data.wipTotalData;
                    var wipBookedData = data.wipBookedData;
                    var wipPaidData = data.wipPaidData;
                    var wipBalanceData = data.wipBalanceData;
                    
                    // {'name': 'Total', 'wip_revenue': 40000, 'wip_cost': 3400, 'margin': 2300}
                    var wipTotalGrandData = data.wipTotalGrandData;
                    var wipBookedGrandTotalData = data.wipBookedGrandTotalData;
                    var wipPaidGrandTotalData = data.wipPaidGrandTotalData;
                    var wipGrandBalanceData = data.wipGrandBalanceData;
                    var wipGroupData = data.wipGroupData;
                    // {'agency':{
                      // # 'name': 'Agency', 
                      // # 'wip_revenue': 10000, 
                      // # 'wip_cost': 10000, 
                      // # 'margin': 10000
                      // # }, 
                      //'transport':{
                    // # 'name': 'Agency', 
                    // # 'wip_revenue': 10000, 
                    // # 'wip_cost': 10000, 
                    // # 'margin': 10000
                    // # },...}
                    // var wipBookedData = data.wipBookedData.data // [{'name': 'Agency', 'wip_revenue': 10000, 'wip_cost': 10000, 'margin': 10000}, ...] 
                    // // var wipBookedData = JSON.parse(data.wipBookedData).data // [{'name': 'Agency', 'wip_revenue': 10000, 'wip_cost': 10000, 'margin': 10000}, ...] 
                    // var wipPaidData = JSON.parse(data.wipPaidData).data // [{'name': 'Agency', 'wip_revenue': 10000, 'wip_cost': 10000, 'margin': 10000}, ...] 
                    // var wipBalanceData = JSON.parse(data.wipBalanceData).data // [{'name': 'Agency', 'wip_revenue': 10000, 'wip_cost': 10000, 'margin': 10000}, ...]
                    console.log('What is my group data ',wipGroupData)
                    
                    if ($('#dashboard_view_text').val() == 'WIP_VIEW'){
                      generate_wip_group_table(wipGroupData)
                      
                      generate_wip_table(
                        'total_wip_body',
                        wipTotalData,
                        wipTotalGrandData,
                      );
                      generate_wip_table(
                        'wip_booked_body',
                        wipBookedData,
                        wipBookedGrandTotalData,
                      );
                      generate_wip_table(
                        'wip_paid_body',
                        wipPaidData,
                        wipPaidGrandTotalData
                      );
                      generate_wip_table(
                        'wip_balance_body',
                        wipBalanceData,
                        wipGrandBalanceData
                      );
                    }
                    
                    // var frame_agreement_x = data.frame_agreement_x 
                    // var frame_agreement_y = data.frame_agreement_y 
                    //TODO generate_frame_agreement_chart(data)

                    console.log(`dynamic realtime display====> ${project_type_name} ${project_budget} ${project_revenue} ${month_label} ${project_counter_item} `)
                    // display table 
                    //TODO generate_table_entries(group_project_table, 'table_customer_info_id');
                    
                    // GENERATING TABLE FOR MMR
                    //TODO generate_table_entries(group_project_table, 'mmr_table_customer_info_id');
                    // Display charts
                    
                    // display line chart

                    jQuery('#LineChartDiv').append(jQuery('<canvas id="LineChart"></canvas>')) 
 
                    var LineOtherProperties = {
                      'backgroundColor': ['rgba(232, 5, 43, 0.839)'],
                      'borderWidth': 3, 'borderColor': '#ffffff',
                      'borderRadius': 0, 'borderSkipped': false,
                      'options': {
                        scales: {
                          y: {
                            beginAtZero: true
                          }
                        }
                      }, 
                    }
                    generate_realtime_charts(
                      project_type_name,
                      project_revenue,
                      'LineChart',
                      'line',
                      'Line Chart',
                      LineOtherProperties,
                    );
                    
                    // PIE CHART STARTS
                    $('#doughnutCanvasDiv').append($(
                      '<h6>File budget </h6>\
											<p class="text-black">Shows the total budget for files</p>\
											<canvas id="doughnutCanvas"></canvas> \
											<a class="text-sm font-weight-bold mb-0 icon-move-right mt-auto" href="/web">\
											Click here\
											<i class="fa fa-arrow-right text-sm ms-1" aria-hidden="true"></i>\
											</a>'
                    ))
                    var PieOtherProperties = {
                      'backgroundColor': [
                        'rgba(232, 5, 43, 0.839)',
                        'rgba(107, 27, 197, 0.89)',
                        'rgba(24, 228, 201, 0.89)',
                        'rgba(175, 207, 87, 0.89)',
                        'rgba(218, 8, 36, 0.89)',
                        'rgba(129, 39, 117, 0.89)',
                        'rgba(10, 41, 82, 0.89)',
                        'rgba(35, 103, 190, 0.89)',
                        'rgba(4, 187, 80, 0.89)',
                        'rgba(rgba(158, 47, 64, 0.733)',
                        ],
                      'borderWidth': 1, 'borderColor': '#ffffff',
                      'borderRadius': 0, 'borderSkipped': false,
                      'options': {
                        scales: {
                          y: {
                            beginAtZero: true
                          }
                        }
                      }, 
                    }
                    generate_realtime_charts(
                      project_type_name,
                      project_budget,
                      'doughnutCanvas',
                      'doughnut',
                      'Chart',
                      PieOtherProperties,
                    );

                    // BAR CHART START
                    $('#chartbarsDiv').append($(
                      '<canvas id="chart-bars" class="chart-canvas text-white" height="200"></canvas>'
                    ));
                    var barOtherProperties = {
                      'backgroundColor': [
                        'rgba(249, 248, 248, 0.983)'
                        ],
                      'borderWidth': 1, 'borderColor': '#ffffff',
                      'borderRadius': 0, 'borderSkipped': false,
                      'hoverBorderColor': "orange", 'maxBarThickness': 10,
                      'tension': 0.4,
                        'options': {
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                          legend: {
                              display: true,
                          }
                          },
                          interaction: {
                          intersect: false,
                          mode: 'index',
                          },
                          scales: {
                              y: {
                                  grid: {
                                  drawBorder: false,
                                  display: false,
                                  drawOnChartArea: false,
                                  drawTicks: false,
                                  },
                                  ticks: {
                                  suggestedMin: 0,
                                  suggestedMax: 500,
                                  beginAtZero: true,
                                  padding: 15,
                                  font: {
                                      size: 14,
                                      family: "Open Sans",
                                      style: 'normal',
                                      lineHeight: 2
                                  },
                                  color: "#fff"
                                  },
                              },
                              x: {
                                  grid: {
                                  drawBorder: false,
                                  display: false,
                                  drawOnChartArea: false,
                                  drawTicks: false
                                  },
                                  ticks: {
                                  display: false
                                  },
                              },
                          },
                      },
                    }
                    generate_realtime_charts(
                      project_counter_item,
                      project_counter,
                      'chart-bars',
                      'bar',
                      'Project Progress Rate',
                      barOtherProperties,
                    );

                    // TICK LINE CHART HERE 
                    // TICK LINE CHART START
                    $('#tickchartlineDiv').append($(
                      '<canvas id="tickchart-line" class="chart-canvas" height="300"></canvas>'
                    ));
                    var tickLinechart = document.getElementById("tickchart-line").getContext("2d");
                    var gradientStroke1 = tickLinechart.createLinearGradient(0, 230, 0, 50);
                    gradientStroke1.addColorStop(1, 'rgba(235, 8, 8, 0.912)');
                    gradientStroke1.addColorStop(0.2, 'rgba(254, 136, 136, 0.912)');
                    gradientStroke1.addColorStop(0, 'rgb(250, 247, 247)'); //purple colors

                    var gradientStroke2 = tickLinechart.createLinearGradient(0, 230, 0, 50);

                    gradientStroke2.addColorStop(1, 'rgb(62, 27, 27)');
                    gradientStroke2.addColorStop(0.2, 'rgba(72,72,176,0.0)');
                    gradientStroke2.addColorStop(0, 'rgba(20,23,39,0)'); //purple colors

                    new Chart(tickLinechart, {
                    type: "line",
                    data: {
                        labels: month_label,
                        datasets: [{
                            label: "Revenue Success Rate",
                            tension: 0.4,
                            borderWidth: 0,
                            pointRadius: 0,
                            borderColor: "#cb0c9f",
                            borderWidth: 3,
                            backgroundColor: gradientStroke1,
                            fill: true,
                            data: month_sales_amount, //[50, 40, 300, 220, 500, 250, 400, 230, 500],
                            maxBarThickness: 6
                        },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                        legend: {
                            display: false,
                        }
                        },
                        interaction: {
                        intersect: false,
                        mode: 'index',
                        },
                        scales: {
                        y: {
                            grid: {
                            drawBorder: false,
                            display: true,
                            drawOnChartArea: true,
                            drawTicks: false,
                            borderDash: [5, 5]
                            },
                            ticks: {
                            display: true,
                            padding: 10,
                            color: '#b2b9bf',
                            font: {
                                size: 11,
                                family: "Open Sans",
                                style: 'normal',
                                lineHeight: 2
                            },
                            }
                        },
                        x: {
                            grid: {
                            drawBorder: false,
                            display: false,
                            drawOnChartArea: false,
                            drawTicks: false,
                            borderDash: [5, 5]
                            },
                            ticks: {
                            display: true,
                            color: '#b2b9bf',
                            padding: 20,
                            font: {
                                size: 11,
                                family: "Open Sans",
                                style: 'normal',
                                lineHeight: 2
                            },
                            }
                        },
                        },
                    },
                    });
                  $.unblockUI()
                })
            },
         },
    });
});