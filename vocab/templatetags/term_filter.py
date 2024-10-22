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

