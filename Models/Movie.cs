using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace EksiCaciklar.Models
{
    public class Movie
    {
        public int Id { get; set; }

        [Required]
        [Display(Name = "Film Adı")]
        public string? Title { get; set; }

        [Display(Name = "Açıklama")]
        public string? Description { get; set; }

        [Display(Name = "Yönetmen")]
        public string? Director { get; set; }

        [Display(Name = "Afiş URL")]
        public string? ImageUrl { get; set; }

        [Display(Name = "Vizyon Tarihi")]
        [DataType(DataType.Date)]
        public DateTime ReleaseDate { get; set; }

        // --- YÖNETİCİ PUANLARI ---
        [Range(0, 100)] public int ScoreScenario { get; set; }
        [Range(0, 100)] public int ScoreActing { get; set; }
        [Range(0, 100)] public int ScoreVisuals { get; set; }
        [Range(0, 100)] public int ScoreSound { get; set; }
        [Range(0, 100)] public int ScoreEditing { get; set; }

        // --- HALK ORTALAMALARI ---
        public double UserAvgScenario { get; set; }
        public double UserAvgActing { get; set; }
        public double UserAvgVisuals { get; set; }
        public double UserAvgSound { get; set; }
        public double UserAvgEditing { get; set; }

        public int VoteCount { get; set; }

        public ICollection<UserVote> UserVotes { get; set; } = new List<UserVote>();


        // --- HESAPLAMALAR ---
        [NotMapped]
        public double AdminScore => (ScoreScenario + ScoreActing + ScoreVisuals + ScoreSound + ScoreEditing) / 5.0;

        [NotMapped]
        public double UserScore => VoteCount == 0 ? 0 : (UserAvgScenario + UserAvgActing + UserAvgVisuals + UserAvgSound + UserAvgEditing) / 5.0;

        [NotMapped]
        public double CacikScore
        {
            get
            {
                if (VoteCount == 0 && AdminScore == 0) return -1;
                if (VoteCount == 0) return AdminScore;
                if (AdminScore == 0) return UserScore;
                return (AdminScore + UserScore) / 2.0;
            }
        }
    }
}