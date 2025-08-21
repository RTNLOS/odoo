/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";


$(document).ready(function () {

	// var toolTip = function(){
	// 	document.addEventListener('DOMContentLoaded', () => {
	// 		// Create a tooltip element
	// 		const tooltip = document.createElement('div');
	// 		tooltip.style.relative = 'absolute';
	// 		tooltip.style.backgroundColor = 'black'; //#333
	// 		tooltip.style.color = '#fff';
	// 		tooltip.style.padding = '3px';
	// 		tooltip.style.borderRadius = '5px';
	// 		tooltip.style.fontSize = '12px';
	// 		tooltip.style.visibility = 'hidden';
	// 		tooltip.style.zIndex = '1000';
	// 		tooltip.style.pointerEvents = 'none';
	// 		document.body.appendChild(tooltip);
		
	// 		// Add event listeners to the div element
	// 		const elements = $('.tooltip-container');
	// 		elements.forEach(element => {
	// 			element.addEventListener('mouseenter', (event) => {
	// 				const tooltipText = element.getAttribute('data-tooltip');
	// 				tooltip.textContent = tooltipText;
	// 				tooltip.style.visibility = 'visible';
	// 			});
		
	// 			element.addEventListener('mousemove', (event) => {
	// 				tooltip.style.left = `${event.pageX + 10}px`;
	// 				tooltip.style.top = `${event.pageY + 10}px`;
	// 			});
		
	// 			element.addEventListener('mouseleave', () => {
	// 				tooltip.style.visibility = 'hidden';
	// 			});
	// 		});
	// 	});
	// }
	// toolTip();
	var formatCurrency = function(value) {
        if (value) {
            var result = value.toString().replace(/D/, "").replace(/\B(?=(\d{3})+(?!\d))/g, ",")
			result = result === undefined ? '' : result
            return result// == undefined ? 0 : result 
        }
    };
	let currency_name = 'NGN';

    if ($('#NGN').prop('checked')) {
      $('#USD').prop('checked', false);
      currency_name = 'NGN';
    }

    if ($('#USD').prop('checked')) {
      $('#NGN').prop('checked', false);
      currency_name = 'USD';

    }

	let get_selected_currency = function(){
		let currency_name = $('#NGN').prop('checked') ? 'NGN' : 'USD'
		console.log('WHAT IS CURRENCY ==== ', currency_name)
		return currency_name
	}

	var convert_long_numbers = function(val){
		let formattedNumber = '0.00'
		if(val){
			var inputVal = val.replace(/,/g, '').replace(/(\.\d*)\./g, '$1');
			formattedNumber = parseFloat(inputVal).toFixed(2);} 
		return formattedNumber;
		}
		

	$(window).scroll(function() {
		// Check the scroll position
		console.log('SCROLLING')

		if ($(this).scrollTop() === 0) {
			console.log('TOPBAR GOING OFF')
			$('.topbar').hide();
		} else {
			console.log('TOPBAR COMING ON')
			$('.topbar').show();
		}
	});

	var renderFileAdmin = async function(){

		$('#fileAdminDiv').empty();

		$('.clickApplyFileAdmin').removeClass('d-none');
		$('#fileAdminDiv').removeClass('d-none');
		$('#generalOverviewCard').addClass('d-none');
		$('#frameAgreementDiv').addClass('d-none');
		$('#mmrTableDiv').addClass('d-none');
		$('#wipTableDiv').addClass('d-none');
		$('.clickApply').addClass('d-none');
		$('#wip_menu').removeClass('d-none');
		$('.clickApplyMmr').addClass('d-none');
		$('.clickApplyFrame').addClass('d-none');
		
		document.getElementById("mysidebar").style.width = "0px";
		$.blockUI({
			'message': '<h2 class="card-name">Please wait ...</h2>'
		});
		await jsonrpc('/display-file-admin', {
			project: $('#memoProjectFilter').val(),
			project_file_type: $('#memoProjectFilter').val(),
			customer_name: $('#memoCustomerFilter').val(),
			currency_name: get_selected_currency(),
			code: $('#searchdashboard_val').val(),
			year: $('#memoYearFilter').val(),
			branch: $('#memoBranchFilter').val(),
			month: $('#memoMonthFilter').val(),
			is_json: 'yes',
		}).then(function(data){
			console.log('pulling data for frame agreement  ', data)
			
			generateFileAdminDashboard(data);
			// Display charts
			$.unblockUI()
		});
	}

	var generateFileAdminDashboard = function(data){
		
		$('#fileAdminDiv').append(`<div class="mycard col-lg-12 col-md-12 pl-5 mb-md-0 mb-4">
			<div class="card">
				<div class="card-header pb-0 mb-2">
					<div class="row">
						<div class="col-lg-6 col-7 mb-2">
							<h2>${data.company_name}</h2>
							<p class="text-sm mb-0">
								<i class="fa fa-check text-info" aria-hidden="true"></i>
								<span class="font-weight-bold ms-1">File Administration</span> 
							</p>
						</div>
					</div>
					<div class="row">
						<div class="col-sm-3 col-md-4 pb-2 cardfile">	
							<div class="number clickcard" id="output_opened_files" value="${data.output_opened_files.records}">${data.output_opened_files.count}</div>
							<div class="card-name">Active files</div>
						</div>
						<div class="col-sm-9 col-md-4 pb-2 cardfile">
							<div class="number clickcard" id="closed_file_ids" value="${data.closed_file_ids.records}">${data.closed_file_ids.count}</div>
							<div class="card-name">Closed files</div>
						</div>
						<div class="col-sm-9 col-md-4 pb-52 cardfile">
							<div class="number clickcard" id="past_one_month_ids" value="${data.past_one_month_ids.records}">${data.past_one_month_ids.count}</div>
							<div class="card-name">Over Due Files</div>
						</div>
					</div>
					<div class="row">
						<div class="col-sm-3 col-md-3 pb-2 cardfile">	
							<div class="number clickcard" id="files_to_be_closeds" value="${data.files_to_be_closeds.records}">${data.files_to_be_closeds.count}</div>
							<div class="card-name">Files to be closed</div>
						</div>
						<div class="col-sm-9 col-md-3 pb-2 cardfile">
							<div class="number clickcard" id="files_to_be_approveds" value="${data.files_to_be_approveds.records}">${data.files_to_be_approveds.count}</div>
							<div class="card-name">Files to be approved</div>
						</div>
						<div class="col-sm-9 col-md-3 pb-2 cardfile">
							<div class="number clickcard" id="pos_to_be_approved_ids" value="${data.pos_to_be_approved_ids.records}">${data.pos_to_be_approved_ids.count}</div>
							<div class="card-name">Pos to be approved</div>
						</div>
					</div>
					<div class="row">
						<div class="col-sm-3 col-md-4 pb-2 cardfile">	
							<div class="number clickcard" id="so_payment_not_registereds" value="${data.so_payment_not_registereds.records}">${data.so_payment_not_registereds.count}</div>
							<div class="card-name">SO Payment not registered</div>
						</div>
						<div class="col-sm-9 col-md-4 pb-2 cardfile">
							<div class="number clickcard" id="files_wto_cost" value="${data.files_wto_cost.records}">${data.files_wto_cost.count}</div>
							<div class="card-name">Files without Cost Budget</div>
						</div>
						<div class="col-sm-9 col-md-4 pb-2 cardfile">
							<div class="number clickcard" value="${data.files_wto_rev.records}">${data.files_wto_rev.count}</div>
							<div class="card-name">Files without revenue budget</div>
						</div>
					</div>
					<div class="row">
						<div class="col-sm-3 col-md-6 pb-2 cardfile">	
							<div class="number clickcard" id="pos_to_be_approved_ids" value="${data.pos_to_be_approved_ids.records}">${data.pos_to_be_approved_ids.count}</div>
							<div class="card-name">Vendor invoices to be validated</div>
						</div>
						<div class="col-sm-9 col-md-6 pb-2 cardfile">
							<div class="number clickcard" id="pos_to_be_paid_ids" value="${data.pos_to_be_paid_ids.records}">${data.pos_to_be_paid_ids.count}</div>
							<div class="card-name">Po to be Paid</div>
						</div>
					</div>
				</div>
			</div>
		</div>`)
	}

	var generate_MMR_table_entries = function(data){
		console.log(data);
		/** records = [{'procurement': 
							{'Department': 'Procurement', 'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 646880.0, 'Jun': 5049900.0, 'Jul': 0, 'Aug': 0, 'Sep': 0, 'Oct': 0, 'Nov': 75.0, 'Margin': 5696855.0},
							},

						{'travel': 
							{'Department': 'Travel', 'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 646880.0, 'Jun': 5049900.0, 'Jul': 0, 'Aug': 0, 'Sep': 0, 'Oct': 0, 'Nov': 75.0, 'Margin': 5696855.0},
							},
			**/
		$('#mmr-tr').empty();
		$('#mmr-tbody').empty();
		// var header_value = data.headers; //['Department', 'Jan', 'Feb', '...','SubTotal', 'Margin']
		var ColumnGrandTotal = {} // 'Jan': 0
		
		// building headers //['Department', 'Jan', 'Feb', '...','SubTotal', 'Margin']
		$.each(data.headers, function (header) { // 
			$('#mmr-tr').append(
				`
					<th class="text-end">
						<span class="text-bold">${data.headers[header]}</span>
					</th>
				`
			)
			ColumnGrandTotal[data.headers[header]] = 0
		}); 
		

		/** data.records = [{'procurement': 
							{'Department': 'Procurement', 'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 646880.0, 'Jun': 5049900.0, 'Jul': 0, 'Aug': 0, 'Sep': 0, 'Oct': 0, 'Nov': 75.0, 'Margin': 5696855.0},
							},

						{'travel': 
							{'Department': 'Travel', 'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0, 'May': 646880.0, 'Jun': 5049900.0, 'Jul': 0, 'Aug': 0, 'Sep': 0, 'Oct': 0, 'Nov': 75.0, 'Margin': 5696855.0},
							},
			**/
		$.each(data.records, function(pr, mnt){
			console.log(`data records IS ${data.records}`);
			var table_row = ``
			$.each(mnt, function(kn, vn){
				console.log(`KN IS ${kn} ${vn}`); //mnt is the key: cfwd,transport
				// i.e kn is Department or Jan, vn is value

				$.each(vn, function(k,v){
					console.log(`K IS ${k} ${v}`);
					// where K is 'JAN': and v is Value i.e 'JAN': 340, 'FEB': 10,... 'Margin': 350 
					if (typeof(v) == 'number'){
						ColumnGrandTotal[k] += v
					}else{
						ColumnGrandTotal[k] = ''
					}
					
					var res = v == 0 ? '-': v; // e.g replace 0 value with -
					// var result = typeof(res) == 'number' ? formatCurrency(Math.ceil(res * 100) / 100) : res
					var result = typeof(res) == 'number' ? formatCurrency(Math.ceil(res)) : res
					table_row += `<td>
						<strong>${result}</strong>
					</td>`
				})
			});
			$('#mmr-tbody').append(
				`<tr class="text-end">
					${table_row}
				</t>
			`)
			console.log(table_row);
		});
		console.log(ColumnGrandTotal)
		
		var grandtotalRow = ``
		$.each(ColumnGrandTotal, function(k, v){
			console.log(v)
			var res = v == 0 ? '-': v; // e.g replace 0 value with - and converting v to the nearest two decimal
			
			grandtotalRow += `<td>
							<strong>${typeof(res) == 'number' ? formatCurrency(Math.ceil(res)) : res}</strong>
						</td>`
						// result == undefined ? '': result
		});
		$('#mmr-tbody').append(
			`<tr class="accounthead text-end">
				${grandtotalRow}
			</t>
		`)
	};
 

	var generate_frame_agreement_chart = function(datax){
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
		/////////////////////////////////////////////////////////////////////////////////
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
		$('#fr_budget_text').text(fr_budget_text);
      	$('#fr_invoice_text').text(fr_invoice_text);
      	$('#budget_percentage').text(formatCurrency(datax.frame_agreement_y[1]));
      	$('#invoice_percentage').text(formatCurrency(datax.frame_agreement_y[0]));
	}
 
	PublicWidget.registry.OfficeDashboard = PublicWidget.Widget.extend({
				selector: '#office-dashboard-content',
				start: function(){
						var self = this;
						return this._super.apply(this, arguments).then(function(){
								console.log("started form request");
								$('#footer').addClass('d-none');
								$('#o_main_nav').addClass('d-none');
								var y_data_chart = $('#y_data_for_chart').text()
								var x_data_chart = $('#x_data_for_chart').text()
								$.blockUI({
									'message': '<h2 class="card-name">Please wait ...</h2>'
								});
								
								var line_doughnut_filter = $('#line_doughnut_filter').text()

								console.log('Y====> ', JSON.parse(y_data_chart).data)
								console.log('X====> ', JSON.parse(x_data_chart).data)
								console.log('X====> ', JSON.parse(line_doughnut_filter))
								var y_data_chart_array = JSON.parse(y_data_chart).data 
								var x_data_chart_array = JSON.parse(x_data_chart).data
								var project_type_name = JSON.parse(line_doughnut_filter).project_type_name
								var project_budget = JSON.parse(line_doughnut_filter).project_budget
								var project_revenue = JSON.parse(line_doughnut_filter).project_revenue
								var month_label = JSON.parse(line_doughnut_filter).month_label 
								var month_sales_amount = JSON.parse(line_doughnut_filter).month_sales_amount 
								var project_counter_item = JSON.parse(line_doughnut_filter).project_counter_item 
								var project_counter = JSON.parse(line_doughnut_filter).project_counter 
								var customer_name = JSON.parse(line_doughnut_filter).customer_name
								var customer_budget = JSON.parse(line_doughnut_filter).customer_budget
								var customer_revenue = JSON.parse(line_doughnut_filter).customer_revenue
								
								console.log('fffy====> ', project_revenue)
								console.log('X====> ', project_type_name)

								if (y_data_chart_array && x_data_chart_array){
										var lineChartGraph = document.getElementById("LineChart").getContext("2d");
										new Chart(lineChartGraph, {
												type: 'line',
												data: {
													labels: project_type_name,
													datasets: [{
														label: '# of ',
														data: project_revenue,
														borderWidth: 1,
														backgroundColor: [
																'rgba(232, 5, 43, 0.839)'
														]
													}]
												},
												options: {
													scales: {
														y: {
															beginAtZero: true
														}
													}
												}
											});
										
										var doughnut = document.getElementById("doughnutCanvas").getContext("2d");
										new Chart(doughnut, {
												type: 'doughnut',
												data: {
													labels: project_type_name,
													datasets: [{
														label: '# of',
														data: project_budget,
														borderWidth: 1,
														// rotation: 270,
														// circumference: 180,
														// cutout: '80%', 
														backgroundColor: [
																'rgba(44, 253, 44, 0.839)',
														'rgba(70, 1, 148, 0.89)',
														'rgba(24, 228, 201, 0.89)',
														'rgba(175, 207, 87, 0.89)',
														'rgba(218, 8, 8, 0.89)',
														'rgba(131, 61, 122, 0.89)',
														'rgba(2, 36, 82, 0.89)',
														'rgba(35, 103, 190, 0.89)',
														'rgba(4, 187, 80, 0.89)',
														'rgba(2, 128, 201, 0.733)',
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
												}
										}); 

									var TickLineChart2 = document.getElementById("chart-bars").getContext("2d");
									new Chart(TickLineChart2, {
											type: 'bar',
											data: {
												labels: project_counter_item, //['Redx', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
												datasets: [{
													label: "Project Progress Rate",
													tension: 0.4,
													borderWidth: 0,
													borderRadius: 4,
													borderSkipped: false,
													// backgroundColor: "#fff",
													backgroundColor: [
															'rgba(249, 248, 248, 0.983)'
													],
													data: project_counter, // [450, 200, 100, 220, 500, 800],
													maxBarThickness: 10,
													hoverBorderColor: "orange",
													}, ],
											},
											options: {
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
									});
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
											//   labels: ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
											labels: month_label,
											datasets: [{
													label: "Success Rate",
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
											// {
											//     label: "Success Rate",
											//     tension: 0.4,
											//     borderWidth: 0,
											//     pointRadius: 0,
											//     borderColor: "#3A416F",
											//     borderWidth: 3,
											//     backgroundColor: gradientStroke2,
											//     fill: true,
											//     data: y_data_chart_array,
											//     maxBarThickness: 6
											// },
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
								}
							$.unblockUI()
						});

				},
				willStart: function(){
					var self = this; 

					return this._super.apply(this, arguments).then(function(){
						$.blockUI({
							'message': '<h2 class="card-name">Please wait ...</h2>'
						});
						console.log("united bosses.....");
						$('#memoCustomerFilter').val('');
						$('#memoProjectFilter').val('');
						$('#memoMonthFilter').val('');
						$('#memoYearFilter').val('');
						$('#memoBranchFilter').val('');
						$('#memoFRFilter').val('');
						$.unblockUI()
					})
				},
				events: {
						'click .btn-close-success': function(ev){
								$('#successful_alert').hide()
						},

						// /get-data-info/

						'click .clickcard': async function(ev){
							var cardElm = $(ev.target);
							console.log('tester', cardElm)
							var value = cardElm.attr('value');
							console.log('tester2', value)

							var url = `/get-data-info/${value}`
							window.open(url, '_blank');
							// window.location.href = 
							// await jsonrpc(`/get-data-info/${cardElm}`, {
							// }).then(function(){

							// })
						},

						'click .li_mmr': async function(ev){
							$('.clickApplyMmr').removeClass('d-none');
							$('#mmrTableDiv').removeClass('d-none');

							$('#generalOverviewCard').addClass('d-none');
							$('#frameAgreementDiv').addClass('d-none');
							$('#fileAdminDiv').addClass('d-none');
							$('.clickApply').addClass('d-none');
							$('.clickApplyFrame').addClass('d-none');
							$('#wipTableDiv').addClass('d-none');
							$('#wip_menu').removeClass('d-none');
							$('.clickApplyFileAdmin').addClass('d-none');
							document.getElementById("mysidebar").style.width = "0px";
							// $('#mmrTableDiv').empty();
							// fetch data
							$.blockUI({
								'message': '<h2 class="card-name">Please wait ...</h2>'
							});
							await jsonrpc('/display-mmr-data', {
								project: $('#memoProjectFilter').val(),
								memo_project_type: $('#memoProjecttypeFilter').val(),
								project_file_type: $('#memoProjectFilter').val(),
								customer_id: $('#memoCustomerFilter').val(),
								code: $('#searchdashboard_val'),
								currency_name: get_selected_currency(),
								// date_from: $('#date_from'),
								// date_to: $('#date_to'),
								year: $('#memoYearFilter').val(),
								branch: $('#memoBranchFilter').val(),
								month: $('#memoMonthFilter').val(),
								is_json: 'yes',
							}).then(function(data){
									console.log(`pulling data for mmr ---${data}`)
									// GENERATING TABLE FOR MMR 
									let yr = $('#memoYearFilter').val()
									let mtn = $('#memoMonthFilter').val()
									let curr_text = $("#reportYear").text()
									let yearReport = `${$('#memoMonthFilter').val()} - ${$('#memoYearFilter').val()}`
									let word = yr || mtn ? yearReport : curr_text
									$("#reportYear").text(word)
									generate_MMR_table_entries(data);
									// Display charts
									$.unblockUI()
							});
						},
						'click .wipApply': async function(ev) {
							$('#dashboard_view_text').val('WIP_VIEW');
							$('.clickApply').removeClass('d-none');
							$('#wipTableDiv').removeClass('d-none');
							$('.clickApplyFileAdmin').addClass('d-none');
							$('.clickApplyFrame').addClass('d-none');
							$('.clickApplyMmr').addClass('d-none');
						},
						'click .li_frame_agreement': async function(ev){
							$('.clickApplyFrame').removeClass('d-none');
							$('#frameAgreementDiv').removeClass('d-none');
							$('#fileAdminDiv').addClass('d-none');
							$('#generalOverviewCard').addClass('d-none');
							$('#mmrTableDiv').addClass('d-none');
							$('.clickApply').addClass('d-none');
							$('.clickApplyMmr').addClass('d-none');
							$('#wipTableDiv').addClass('d-none');
							$('#wip_menu').removeClass('d-none');
							$('.clickApplyFileAdmin').addClass('d-none');
							$.blockUI({
								'message': '<h2 class="card-name">Please wait ...</h2>'
							});
							document.getElementById("mysidebar").style.width = "0px";
							await jsonrpc('/display-frame-agreeement', {
								project: $('#memoProjectFilter').val(),
								project_file_type: $('#memoProjectFilter').val(),
								customer_name: $('#memoCustomerFilter').val(),
								currency_name: currency_name,
								code: $('#searchdashboard_val').val(),
								year: $('#memoYearFilter').val(),
								branch: $('#memoBranchFilter').val(),
								month: $('#memoMonthFilter').val(),
								is_json: 'yes',
							}).then(function(data){
									console.log('frame date pulling ', data)
									// GENERATING FRAME AGREEMENT CHART
									generate_frame_agreement_chart(data);
									// Display charts
									$.unblockUI()

							});
						},
						'click .li_overview_dashboard': function(ev){
							// $('#generalOverviewCard').removeClass('d-none');
							$('.clickApply').removeClass('d-none');
							$('.clickApplyFrame').addClass('d-none');
							$('.clickApplyFileAdmin').addClass('d-none');
							$('.clickApplyMmr').addClass('d-none');
							$('#wipTableDiv').addClass('d-none');
							$('.fileAdminDiv').addClass('d-none');

							$('#frameAgreementDiv').addClass('d-none');
							$('#mmrTableDiv').addClass('d-none');
							$('#wip_menu').removeClass('d-none');
							document.getElementById("mysidebar").style.width = "0px";
							window.location.href = `/my-dashboard`;
						},

						'click .li_project_analytic': function(ev){
							// window.location.href = `/my-dashboard`;
							renderFileAdmin();
						},
						'click .clickApplyFileAdmin': async function(ev){
							renderFileAdmin()
						},
						'click .opennavbtn': function(ev){
								console.log(`Opening of navbar`)
								document.getElementById("mysidebar").style.width = "250px";
								// $('.closenavbtn').removeClass('d-none');
								// $('.opennavbtn').addClass('d-none'); 
						},
						'click .closenavbtn': function(ev){
								console.log(`Closing of navbar`)
								document.getElementById("mysidebar").style.width = "0px";
								$('.opennavbtn').removeClass('d-none');
								$('.closenavbtn').addClass('d-none');
								// document.getElementById("main").style.marginLeft= "0";
						},

						'click .closeSb': function(ev){
								console.log(`Closing of navbar`)
								document.getElementById("mysidebar").style.width = "0px";
								$('.opennavbtn').removeClass('d-none');
								$('.closenavbtn').addClass('d-none');
								// $('.topbar').addClass('d-none');

								if ($('.topbar').hasClass('d-none')){
									$('.topbar').removeClass('d-none');
								}else{
									$('.topbar').addClass('d-none');
								}
						},
						'click .searchdashboardbtn': function(ev){
								console.log("dashboard searching ");
								var search_panel = $("#searchdashboard_val")
								var memo_type = $("#memotypedashboard")
								var get_search_query = search_panel.val();
								var memo_type_val = memo_type.val() != undefined || '' ? '/'+memo_type.val() : '';
								// empty the search panel value
								search_panel.val("");
								window.location.href = `/my-dashboard/${get_search_query}${memo_type_val}`
						},
				 },
		});

// return PortalRequestWidget;
});