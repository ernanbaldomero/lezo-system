"""
Utility functions for Lezo LGU System, including genealogy inference.
Optimized to minimize database queries.
"""

from .models import Relationship

def get_relationships(citizen):
    """
    Get inferred relationships for a citizen (uncles, nephews).
    Direct relationships are handled in views for efficiency.
    Returns a list of (type, related_citizen) tuples.
    """
    inferred = []

    # Inferred relationships: uncles (parent's brothers)
    parents = Relationship.objects.filter(related_citizen=citizen, type__in=['father', 'mother']).select_related('citizen')
    for parent in parents:
        uncles = Relationship.objects.filter(citizen=parent.citizen, type='brother').select_related('related_citizen')
        for uncle in uncles:
            if not any(r[0] == 'uncle' and r[1] == uncle.related_citizen for r in inferred):
                inferred.append(('uncle', uncle.related_citizen))

    # Inferred relationships: nephews (siblings' children)
    siblings = Relationship.objects.filter(citizen=citizen, type='brother').select_related('related_citizen')
    for sibling in siblings:
        nephews = Relationship.objects.filter(citizen=sibling.related_citizen, type__in=['son', 'daughter']).select_related('related_citizen')
        for nephew in nephews:
            if not any(r[0] == 'nephew' and r[1] == nephew.related_citizen for r in inferred):
                inferred.append(('nephew', nephew.related_citizen))

    return inferred