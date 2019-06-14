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
						res=validate_avaialable_bom(name,item.name)
						if not res==False:
							bom_doc=frappe.get_doc("BOM",res)
							idx=len(bom_doc.items)+1
							for row in so_doc.row_materials:
								count=0
								for bom_item in bom_doc.items:
									if bom_item.item_code==row.item_code:
										count += 1
								if count==0:
									add_bom_item(row.item_code,row.item_name,row.uom,row.qty*(item.qty/so_doc.total_qty),res,idx)
									idx += 1
									
							bom_doc_final=frappe.get_doc("BOM",res)
							bom_doc_final.save()
							msg='BOM '+'<a href="#Form/BOM/'+bom_doc_final.name+'">'+bom_doc_final.name+'</a>'+' Updated'
							frappe.msgprint(msg);
						
						else:
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

def validate_avaialable_bom(so_no,si_no):
	so_item=frappe.get_doc("Sales Order Item",si_no)
	bom_details=frappe.db.sql("""select name from `tabBOM` 
		where sales_order=%s and item=%s and docstatus=0 limit 1"""
		,(so_no,so_item.item_code),as_dict=1)
	if len(bom_details)>=1:
		return bom_details[0].name
	else:
		return False
		

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

def add_bom_item(item_code,item_name,uom,qty,name,idx):
	doc=frappe.get_doc(dict(
		doctype="BOM Item",
		parent=name,
		parenttype="BOM",
		parentfield="items",
		item_code=item_code,
		item_name=item_name,
		uom=uom,
		qty=qty,
		rate=0,
		idx=idx
	)).insert()

