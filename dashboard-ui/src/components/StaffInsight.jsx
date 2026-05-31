import { UserX } from 'lucide-react';

export default function StaffInsight() {
  return (
    <aside className="staff-insight glass" aria-label="Staff exclusion">
      <div className="staff-insight-icon">
        <UserX size={20} strokeWidth={2.2} />
      </div>
      <div>
        <strong>Staff-aware analytics</strong>
        <p>
          Black-coat staff are tagged and removed from footfall and conversion — so your rate reflects real shoppers, not employees on the floor.
        </p>
      </div>
    </aside>
  );
}
