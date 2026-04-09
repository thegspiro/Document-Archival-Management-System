/** Role-based action matrix for client-side permission checks. */

const ROLE_HIERARCHY: Record<string, number> = {
  superadmin: 100,
  admin: 80,
  archivist: 60,
  contributor: 40,
  intern: 20,
  viewer: 10,
};

const ACTION_REQUIREMENTS: Record<string, number> = {
  'documents.create': 20,    // intern+
  'documents.edit': 40,      // contributor+
  'documents.delete': 80,    // admin+
  'documents.publish': 60,   // archivist+
  'documents.bulk_delete': 80,
  'vocabulary.manage': 60,   // archivist+
  'users.manage': 80,        // admin+
  'settings.manage': 80,     // admin+
  'exhibitions.create': 60,  // archivist+
  'exhibitions.publish': 80, // admin+
  'review.access': 60,       // archivist+
  'review.approve': 60,
  'imports.manage': 80,      // admin+
  'deaccession.propose': 60,
  'deaccession.approve': 80,
  'annotations.create': 40,  // contributor+
  'annotations.delete_any': 60,
};

export function checkPermission(
  userRoles: string[],
  action: string,
  _resource?: string,
): boolean {
  const maxLevel = Math.max(
    ...userRoles.map((r) => ROLE_HIERARCHY[r] ?? 0),
    0,
  );
  const required = ACTION_REQUIREMENTS[action] ?? 0;
  return maxLevel >= required;
}

export function getAvailableBulkActions(roles: string[]): string[] {
  const actions: string[] = [];
  const maxLevel = Math.max(...roles.map((r) => ROLE_HIERARCHY[r] ?? 0), 0);

  if (maxLevel >= 20) actions.push('apply_terms', 'remove_terms', 'clear_inbox');
  if (maxLevel >= 40) actions.push('assign_node', 'set_public', 'add_to_review');
  if (maxLevel >= 60) actions.push('export_zip');
  if (maxLevel >= 80) actions.push('delete');

  return actions;
}
