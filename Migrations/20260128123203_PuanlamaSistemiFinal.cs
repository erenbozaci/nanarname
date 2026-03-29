using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace EksiCaciklar.Migrations
{
    /// <inheritdoc />
    public partial class PuanlamaSistemiFinal : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.RenameColumn(
                name: "Score",
                table: "UserVotes",
                newName: "ScoreVisuals");

            migrationBuilder.RenameColumn(
                name: "UserScore",
                table: "Movies",
                newName: "UserAvgVisuals");

            migrationBuilder.AddColumn<int>(
                name: "ScoreActing",
                table: "UserVotes",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "ScoreEditing",
                table: "UserVotes",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "ScoreScenario",
                table: "UserVotes",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "ScoreSound",
                table: "UserVotes",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<double>(
                name: "UserAvgActing",
                table: "Movies",
                type: "float",
                nullable: false,
                defaultValue: 0.0);

            migrationBuilder.AddColumn<double>(
                name: "UserAvgEditing",
                table: "Movies",
                type: "float",
                nullable: false,
                defaultValue: 0.0);

            migrationBuilder.AddColumn<double>(
                name: "UserAvgScenario",
                table: "Movies",
                type: "float",
                nullable: false,
                defaultValue: 0.0);

            migrationBuilder.AddColumn<double>(
                name: "UserAvgSound",
                table: "Movies",
                type: "float",
                nullable: false,
                defaultValue: 0.0);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "ScoreActing",
                table: "UserVotes");

            migrationBuilder.DropColumn(
                name: "ScoreEditing",
                table: "UserVotes");

            migrationBuilder.DropColumn(
                name: "ScoreScenario",
                table: "UserVotes");

            migrationBuilder.DropColumn(
                name: "ScoreSound",
                table: "UserVotes");

            migrationBuilder.DropColumn(
                name: "UserAvgActing",
                table: "Movies");

            migrationBuilder.DropColumn(
                name: "UserAvgEditing",
                table: "Movies");

            migrationBuilder.DropColumn(
                name: "UserAvgScenario",
                table: "Movies");

            migrationBuilder.DropColumn(
                name: "UserAvgSound",
                table: "Movies");

            migrationBuilder.RenameColumn(
                name: "ScoreVisuals",
                table: "UserVotes",
                newName: "Score");

            migrationBuilder.RenameColumn(
                name: "UserAvgVisuals",
                table: "Movies",
                newName: "UserScore");
        }
    }
}
