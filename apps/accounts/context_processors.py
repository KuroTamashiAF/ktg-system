from apps.accounts.models import Section


def current_section(request):
    if not request.user.is_authenticated:
        return {'current_section': None}

    if request.user.role in ('admin', 'dispatcher'):
        section_id = request.session.get('viewed_section_id')
        if section_id:
            try:
                section = Section.objects.get(id=section_id)
            except Section.DoesNotExist:
                section = None
        else:
            section = None
    else:
        section = request.user.section

    return {'current_section': section}