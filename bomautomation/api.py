from __future__ import unicode_literals
import frappe, erpnext, math, json
from frappe import _
import traceback

@frappe.whitelist()
def app_error_log(title,error):
	d = frappe.get_doc({
			"doctype": "Custom Error Log",
			"title":str("User:")+str(title),
			"error":traceback.format_exc()
		})
	d = d.insert(ignore_permissions=True)
	return d


@frappe.whitelist()
def make_bom(name,selected_items):
	try:
		so_doc=frappe.get_doc("Sales Order",name)
		if len(so_doc.items)>=1:
			if len(so_doc.row_materials)>=1:				
				for item in so_doc.items:
					if item.name in selected_items:
						row_materials=[]
						for row in so_doc.row_materials:
							row_dict={}
							row_dict["item_code"]=row.item_code
							row_dict["item_name"]=row.item_name
							row_dict["uom"]=row.uom
							row_dict["qty"]=row.qty*(item.qty/so_doc.total_qty)
							row_materials.append(row_dict)
						create_bom(item.item_code,row_materials,so_doc.company,so_doc.currency,item.qty,so_doc.name)
			else:
				frappe.throw("Row Materials Required For Generate BOM")
		else:
			frappe.throw("Items Required For Generate BOM")

	except Exception as e:
		error_log=app_error_log(frappe.session.user,str(e))

def create_bom(item,item_details,company,currency,qty,sales_order):
	try:
		bom_doc=frappe.get_doc(dict(
			doctype="BOM",
			company=company,
			currency=currency,
			item=item,
			items=item_details,
			quantity=qty,
			rm_cost_as_per="Valuation Rate",
			sales_order=sales_order
		)).insert()
		msg='BOM '+'<a href="#Form/BOM/'+bom_doc.name+'">'+bom_doc.name+'</a>'+' Created'
		frappe.msgprint(msg);

	except Exception as e:
		frappe.errprint(json.dumps(item_details))
		error_log=app_error_log(frappe.session.user,str(e))
