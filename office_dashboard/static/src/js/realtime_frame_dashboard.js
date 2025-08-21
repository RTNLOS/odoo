/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
$(document).ready(function () {
  var formatCurrency = function(value) {
        if (value) {
            var result = value.toString().replace(/D/, "").replace(/\B(?=(\d{3})+(?!\d))/g, ",")
            return result// == undefined ? 0 : result 
        }
    };
    let currency_name = 'NGN';
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


    var generate_realtime_charts = function(
      x_axis, y_axis, canvasId, chartType, displayLabel, other_properties=null){
      var chartObject = document.getElementById(canvasId).getContext("2d");
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

    var generate_frame_agreement_chart = function(datax){
		// guageChartCanvas

        ////////////////////////////////////////////////////////
        ////
		var budget_text = datax.frame_agreement_budget; // data.frame_agreement_y.length > 0 ? data.frame_agreement_y[0] : '';
		var currency_symbol = datax.currency_symbol;
		var fr_budget_text = `${currency_symbol} ${formatCurrency(budget_text)}`
		var fr_invoice_text = `${currency_symbol} ${formatCurrency(datax.confirmed_so)}`

		let existingChart = Chart.getChart("guageChartCanvas");
		if (existingChart != undefined){
			existingChart.destroy();
		};
		let data = {
			labels: ["Safe", "Risky Zone", "Danger"],
			datasets: [
			  {
				label: "Frame Agreement Guage",
				data: datax.frame_agreement_y, //[80, 20, 20] ,
				backgroundColor: [
				  "rgba(75, 192, 192, 0.8)",
				  "rgba(255, 206, 86, 0.8)",
				  "rgba(255, 26, 104, 0.8)",
				],
				needleValue: datax.frameNeedleValue,
				borderColor: "white",
				borderWidth: 2,
				cutout: "95%",
				circumference: 180,
				rotation: 270,
				borderRadius: 5,
			  },
			],
		  };
		  
		  //gaugeNeedle
		let gaugeNeedle2 = {
			id: "gaugeNeedle2",
			afterDatasetDraw(chart, args, options) {
			  const {
				ctx,
				config,
				data,
				chartArea: { top, right, bottom, left, width, height },
			  } = chart;
			ctx.save();
			let dataTotal = data.datasets[0].data.reduce((a, b) => a + b, 0);
			let needleValue_res = data.datasets[0].needleValue == 0 ? 0 : data.datasets[0].needleValue;
			let over_budget = dataTotal + 5 // add 5 to the total of 120 == 125 guage will be over
			let needleValue = needleValue_res > dataTotal ? over_budget : needleValue_res // data.datasets[0].needleValue == 0 ? 0 : data.datasets[0].needleValue;

			// calculating the value of needle
			let circumference = ((chart._metasets[0].data[0].circumference / Math.PI) / data.datasets[0].data[0]) * needleValue;
			let rotationValue = 15.2 // get the value of needle, e.g 80 ; check where i, 2, 3, 4 or 5 falls
			let angle = Math.PI * (circumference + 1.5)
			
			// let angle = needleValue / rotationValue;
			let cx = chart._metasets[0].data[0].x; // width / 2;
			let cy = chart._metasets[0].data[0].y;
			let innerRadius = chart._metasets[0].data[0].innerRadius;
			let outerRadius = chart._metasets[0].data[0].outerRadius;
			let widthSlice = (outerRadius - innerRadius) / 2
			
			  //needle
			  ctx.translate(cx, cy);
			  ctx.rotate(angle); // 1.5 -1.7 is 50 [0, 0.5, 1, 1.5, ]
			  ctx.beginPath();
			  ctx.moveTo(0, -2);
			//   ctx.moveTo(0 - 15, 0);
			//   ctx.lineTo(height - ctx.canvas.offsetTop - 160, 0); // change 160 value if the needle size gets changed
			  ctx.lineTo(0, 0 - innerRadius - widthSlice); // change 160 value if the needle size gets changed
			//   ctx.lineTo(0, 2); 
			  ctx.lineTo(0 + 15, 0); 
			  ctx.fillStyle = "#444";
			  ctx.fill();

			  //needle dot
			  ctx.translate(-cx, -cy);
			  ctx.beginPath();
			  ctx.arc(cx, cy, 20, 2, 10);
			  ctx.fill();
			  ctx.restore();
		  
			  //text
			  ctx.font = "20px Ubuntu";
			  ctx.fillStyle = "#444";
			  let frameDisplayText = `${fr_invoice_text} / ${fr_budget_text}`
			  ctx.fillText(frameDisplayText, cx, cy + 50);
			  ctx.font = "10px Ubuntu";
			  ctx.fillText(0, 5, cy + 20);
			//   ctx.fillText("80%", cx, 90);
			//   ctx.fillText("100%", cx + 185, 200); // change values if the position gets changed
			//   ctx.fillText("120%", cx + 193, 320); // change values if the position gets changed
			  ctx.textAlign = "center";
			  ctx.restore();
			},
		};
		  // config
		let config = {
			type: "doughnut",
			data,
			options: {
			  plugins: {
				legend: {
				  display: false,
				},
				tooltip: {
				  yAlign: "bottom",
				  displayColors: false,
				  callbacks: {
					label: function (tooltipItem, data, value) {
					  return tooltipItem.label;
					},
				  },
				},
			  },
			},
			plugins: [gaugeNeedle2],
		};
		  
		// render init block
		new Chart(document.getElementById("guageChartCanvas"), config);


		/////////////////////////////////////////////////////////////////////////////////

        ///////////////////////////////////////////////////////


		// let existingChart = Chart.getChart("guageChartCanvasTick");
		// if (existingChart != undefined){
		// 	existingChart.destroy();
		// }; 

		// var guageNeedle = {
		// 	id: 'guageNeedle',
		// 	afterDatasetsDraw(chart, args, plugins){
		// 		const {ctx, data, chartArea: { top, right, bottom, left, width, height }} = chart;
		// 		ctx.save();
		// 		console.log(chart);
		// 		// console.log(chart._metasets[0].data[0].x);
		// 		const xCenter = chart._metasets[0].data[0].x; //data.datasets[0].data//chart.getDatasetMeta(0).data[0].x;
		// 		const yCenter = chart._metasets[0].data[0].y; // chart.getDatasetMeta(0).data[0].y;
		// 		const outRadius = chart._metasets[0].data[0].outerRadius; //chart.getDatasetMeta(0).data[0].outerRadius
		// 		const innerRadius = chart._metasets[0].data[0].innerRadius //10; //chart.getDatasetMeta(0).data[0].innerRadius

		// 		const widthSlice = (outRadius - innerRadius) / 3;
		// 		const radius = 15;
		// 		const anglestart = Math.PI / 180;

		// 		ctx.translate(xCenter, yCenter);
		// 		ctx.beginPath(); // remove border on each guage color
		// 		ctx.fillStyle = 'grey';
		// 		ctx.strokeStyle = 'grey';
		// 		ctx.lineWidth = 0.5; // how both the needle will be
		// 		// ctx.moveTo(xCenter, yCenter); // sets this to zero
		// 		ctx.moveTo(0 - 15, 0); // sets this to zero
		// 		ctx.lineTo(0, 0 - innerRadius - widthSlice); // 
		// 		// ctx.lineTo(0 + 15, 0); // creates double needle to be filled
		// 		ctx.lineTo(0 + radius, 0); // creates double needle to be filled
		// 		ctx.closePath(); // fill the bottom of needle
		// 		ctx.stroke();
		// 		ctx.fill();
		// 		ctx.restore();
        //         let cx = width / 2;
		// 	    let cy = chart._metasets[0].data[0].y;


		// 		// add a dot bottom the needle
		// 		ctx.beginPath();
		// 		ctx.arc(0,0,  radius, anglestart, anglestart * 360, false);
        //         // ctx.arc(0,0, radius, anglestart, anglestart * 360, false);
		// 		ctx.fill();


		// 	}
		// } 
		
		// var guageChart = document.getElementById("guageChartCanvasTick").getContext("2d");
		// new Chart(guageChart, {
		// 	type: 'doughnut',
		// 	data: {
		// 		labels: ['Revenue', 'Budget'],
		// 		datasets: [{
		// 			label: '# of',
		// 			data: datax.frame_agreement_fill,
		// 			borderWidth: 1,
		// 			rotation: 270,
		// 			circumference: 180,
		// 			cutout: '80%', 
		// 			backgroundColor: [
		// 					// 'rgb(253, 241, 5)', //yellow
		// 					'rgb(16, 235, 4)',
		// 					'rgba(232, 5, 43, 0.839)',
		// 					// 'rgba(175, 207, 87, 0.89)', 
		// 			]
		// 		}]
		// 	},
		// 	options: {
		// 		scales: {
		// 			y: {
		// 				beginAtZero: true
		// 			}
		// 		},
		// 		aspectRatio: 1.5,
		// 		plugins: {
		// 			legend: {
		// 					display: false
		// 			}
		// 		}
		// 	}
		// });
      var budget_text = datax.frame_agreement_budget // data.frame_agreement_y.length > 0 ? data.frame_agreement_y[0] : '';
      var currency_symbol = datax.currency_symbol;
      $('#fr_budget_text').text(`${currency_symbol} ${formatCurrency(budget_text)}`);
      $('#fr_invoice_text').text(`${currency_symbol} ${formatCurrency(datax.confirmed_so)}`);
      $('#budget_percentage').text(formatCurrency(datax.frame_agreement_y[1]));
      $('#invoice_percentage').text(formatCurrency(datax.frame_agreement_y[0]));
    }

    PublicWidget.registry.realTimeFrame = PublicWidget.Widget.extend({
        selector: '#office-dashboard-content',
        start: function(){
            var self = this;
            return this._super.apply(this, arguments).then(function(){
                console.log("real time frame agreement dashboard loading");
            });

        },
        willStart: function(){
            var self = this; 
            return this._super.apply(this, arguments).then(function(){
                console.log("real time dashboard  3"); 
            })
        },
        events: {
            'change .USD': function(ev){
              let usd = $('#USD');
              if (usd.prop('checked')){
                currency_name = "USD";
                $('#NGN').prop('checked', false);
              }
            },
            'change .NGN': function(ev){
              let ngn = $('#NGN');
              if (ngn.prop('checked')){
                currency_name = "NGN";
                $('#USD').prop('checked', false);
              }
            },
            
            'click .clickApplyFrame': async function(ev){
                let qty_elm = $(ev.target);
                // Empty the already populated values
                // fetch data
                $.blockUI({
                    'message': '<h2 class="card-name">Please wait ...</h2>'
                });
                await jsonrpc('/display-frame-agreeement', {
                  project: $('#memoProjectFilter').val(),
                  project_file_type: $('#memoProjectFilter').val(),
                  customer_name: $('#memoCustomerFilter').val(),
                  currency_name: currency_name,
                  code: $('#searchdashboard_val').val(),
                  year: $('#memoYearFilter').val(),
                  branch: $('#memoBranchFilter').val(),
                  month: $('#memoMonthFilter').val(),
                  frame_agreement_id: $('#memoFRFilter').val(),
                  is_json: 'yes',
                }).then(function(data){
                    // var frame_agreement_x = data.frame_agreement_x 
                    // var frame_agreement_y = data.frame_agreement_y 
                    generate_frame_agreement_chart(data);
                    $.unblockUI()
                })
            },

         },
    });
});