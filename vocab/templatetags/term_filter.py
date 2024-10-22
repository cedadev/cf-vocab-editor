from django import template
from django.utils.safestring import mark_safe

register = template.Library()


print("LOADING>><")


'''{{term.name}}</li>
<li>{{term.description}}</li>
<li>{{term.externalid}}</li>
<li>{{term.unit}}</li>
<li>{{term.unit_ref}}'''

def term_div(term):
    if term is None:
        return "No term"
    if term.externalid:
        external_id = f' <span class="badge bg-secondary">{term.externalid}</span>'
    else:
        external_id = ""

    if term.unit:
        if term.unit_ref:
            unit_str = f' <span class="badge bg-primary">{term.unit} [{term.unit_ref}]</span>'
        else:
            unit_str = f' <span class="badge bg-primary">{term.unit}</span>'
    else:
        unit_str = ""

    x = f'<span class="font-monospace fw-bolder">{term.name}{unit_str}{external_id}</span> <br/><small>{term.description}</small>'
    print(x)
    return mark_safe(x)


register.filter("term_div", term_div)


def alias_span(alias):
    return mark_safe(f'<span class="font-monospace fst-italic fw-bold">{alias.name}</span>')

register.filter("alias_span", alias_span)


def prop_div(prop, edit=False):

    status_badge = f'<span class="badge  prop prop-{prop.status}">{prop.status}</span>'
    term_str = term_div(prop.current_term())
    
    s = f'<div class="prop prop-{prop.status}">{status_badge} {prop.proposer} {term_str}</div>'
    return mark_safe(s)

register.filter("prop_div", prop_div)


def prop_change_div(prop):

    if prop.proposed_date:
        date = prop.proposed_date
    else: 
        date = ""
    status_badge = f'{date} <span class="badge  prop prop-{prop.status}"> {prop.status}</span>'
    term_str = term_div(prop.current_term())
    
    s = f'<div class="prop prop-{prop.status} m-2">{status_badge} {prop.proposer} {term_str} Added to: {prop.vocab_list_version}</div>'
    return mark_safe(s)
register.filter("prop_change_div", prop_change_div)

def prop_change_type_badge(prop):
    updatetype = prop.updatetype()
    if updatetype == 'New':
        return mark_safe('<span class="badge bg-success">New Term</span>')
    elif updatetype == 'Updated':
        return mark_safe('<span class="badge bg-info">Updated term description</span>')
    else:
        return mark_safe(f'<span class="badge bg-warning">Term change from {prop.first_term}</span>')
register.filter("prop_change_type_badge", prop_change_type_badge)

